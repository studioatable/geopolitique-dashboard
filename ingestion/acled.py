#!/usr/bin/env python3
"""
acled.py — Ingestion des événements de conflit ACLED
=====================================================

Module pivot du projet (étape 7 de la roadmap Phase 2). Récupère les événements
de violence politique des 90 derniers jours via l'API ACLED (authentification de
session Drupal — pas de clé API statique), normalise en GeoJSON et calcule
les agrégats par pays × fenêtre temporelle × catégorie.

Stratégie de cache :
    - Si data/conflict/acled_events.geojson existe et a moins de CACHE_TTL_SECONDS
      (24h par défaut), on saute le téléchargement et on retourne le verdict CACHED.
    - Sinon, on télécharge tout en pagination, on normalise et on écrit.

Authentification :
    - Variables d'environnement ACLED_EMAIL et ACLED_PASSWORD chargées via dotenv
      depuis le fichier .env à la racine du projet (jamais committé, dans .gitignore).
    - POST sur /user/login?_format=json puis cookies de session conservés.

Sorties :
    - data/conflict/acled_events.geojson — Features Point minifiées (~10 MB pour 100k events)
    - data/conflict/acled_aggregates.json — agrégats par pays × fenêtre × catégorie (~100 KB)

Usage :
    python ingestion/acled.py [--force]

Code de sortie :
    0 — ingestion réussie ou cache valide
    1 — erreur réseau, authentification ou parsing
    2 — configuration manquante (.env, etc.)

Studio à Table — geopolitique-dashboard
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

SCRIPT_VERSION = "0.7.0"
SOURCE_ID = "acled"
TIMEOUT_SECONDS = 60
USER_AGENT = (
    f"Studio-a-Table-Geopolitique-Ingest/{SCRIPT_VERSION} "
    "(+https://studioatable.fr)"
)

# Endpoints ACLED — authentification OAuth Password Grant
# Note : ACLED a migré son API vers /api/acled/read avec auth OAuth (mai 2026+).
# La session Drupal (login cookie) ne fonctionne plus pour l'API REST, seul
# le Bearer token OAuth est accepté.
ACLED_OAUTH_URL = "https://acleddata.com/oauth/token"
# _format=json directement dans l'URL (conforme exemple Python officiel ACLED)
ACLED_READ_URL = "https://acleddata.com/api/acled/read?_format=json"
ACLED_CLIENT_ID = "acled"
ACLED_OAUTH_SCOPE = "authenticated"

# Paramètres d'ingestion
WINDOW_DAYS = 90  # On télécharge 90 jours puis on agrège par 7/30/90 côté front
PAGE_SIZE = 5000  # max ACLED API
CACHE_TTL_SECONDS = 24 * 3600  # 24 heures

# Catégories d'événements ACLED à conserver (les 6 event_types)
ACLED_EVENT_TYPES = [
    "Battles",
    "Explosions/Remote violence",
    "Violence against civilians",
    "Protests",
    "Riots",
    "Strategic developments",
]

# Sous-ensemble "violence armée stricte" pour l'analyse conflits
VIOLENT_TYPES = {
    "Battles",
    "Explosions/Remote violence",
    "Violence against civilians",
}

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
REGISTRY_PATH = ROOT / "data" / "registry" / "sources.json"
CONFLICT_DIR = ROOT / "site" / "data" / "conflict"       # servi par le sous-domaine
EVENTS_OUTPUT = CONFLICT_DIR / "acled_events.geojson"
AGGREGATES_OUTPUT = CONFLICT_DIR / "acled_aggregates.json"


def cache_is_fresh(force: bool = False) -> bool:
    """Retourne True si le cache est récent et qu'on peut sauter le téléchargement."""
    if force:
        return False
    if not EVENTS_OUTPUT.exists() or not AGGREGATES_OUTPUT.exists():
        return False
    mtime = EVENTS_OUTPUT.stat().st_mtime
    age_seconds = datetime.now().timestamp() - mtime
    return age_seconds < CACHE_TTL_SECONDS


def load_credentials() -> tuple[str, str]:
    """Charge ACLED_EMAIL / ACLED_PASSWORD depuis le .env. Lève une erreur si absent."""
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
    email = os.environ.get("ACLED_EMAIL", "").strip()
    password = os.environ.get("ACLED_PASSWORD", "").strip()
    if not email or not password:
        raise EnvironmentError(
            "Variables ACLED_EMAIL et/ou ACLED_PASSWORD manquantes.\n"
            f"Créer un fichier .env à la racine du projet ({ENV_PATH}) "
            "en suivant .env.example."
        )
    return email, password


def load_source_meta() -> dict:
    """Charge la fiche ACLED du registre local."""
    if not REGISTRY_PATH.exists():
        return {"id": SOURCE_ID, "short_name": "ACLED"}
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        registry = json.load(f)
    for s in registry.get("sources", []):
        if s.get("id") == SOURCE_ID:
            return s
    return {"id": SOURCE_ID, "short_name": "ACLED"}


def open_session(email: str, password: str) -> requests.Session:
    """Ouvre une session ACLED OAuth Password Grant.

    Reçoit un Bearer token valide 24h, qu'on injecte dans le header
    Authorization de la session pour toutes les requêtes /api/acled/read
    suivantes. Le refresh_token reçu n'est pas utilisé (le script tourne
    en moins de 24h, on relogue plutôt que de gérer le refresh)."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    print(f"  → OAuth ACLED ({email}) ...", end=" ", flush=True)
    # ACLED suit le standard OAuth strict : champ "username" attendu
    # (et non "email" malgré ce que dit la doc tierce). Confirmé par
    # le message d'erreur HTTP 400 : "Check the username parameter".
    resp = session.post(
        ACLED_OAUTH_URL,
        data={
            "username": email,
            "password": password,
            "grant_type": "password",
            "client_id": ACLED_CLIENT_ID,
            "scope": ACLED_OAUTH_SCOPE,
        },
        timeout=TIMEOUT_SECONDS,
    )
    if resp.status_code != 200:
        print(f"ÉCHEC (HTTP {resp.status_code})")
        raise RuntimeError(
            f"Authentification OAuth ACLED échouée (HTTP {resp.status_code}). "
            f"Vérifier ACLED_EMAIL / ACLED_PASSWORD dans .env. "
            f"Body: {resp.text[:300]}"
        )
    try:
        payload = resp.json()
    except ValueError:
        raise RuntimeError(f"Réponse OAuth ACLED non-JSON : {resp.text[:300]}")

    access_token = payload.get("access_token")
    expires_in = payload.get("expires_in", 86400)
    if not access_token:
        raise RuntimeError(
            f"OAuth ACLED réussi mais access_token absent : {payload}"
        )
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    print(f"OK (token Bearer, expire dans {expires_in // 3600}h)")
    return session


def fetch_events_window(
    session: requests.Session, start_date: str, end_date: str
) -> list[dict]:
    """Récupère tous les événements ACLED entre start_date et end_date (YYYY-MM-DD)."""
    all_events: list[dict] = []
    page = 1
    print(f"  → Téléchargement événements {start_date} → {end_date} ...")
    # Headers conformes à l'exemple Python officiel ACLED
    # (Content-Type explicite même sur GET, c'est ce que leur doc montre).
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    while True:
        params = {
            "event_date": f"{start_date}|{end_date}",
            "event_date_where": "BETWEEN",
            "limit": PAGE_SIZE,
            "page": page,
        }
        resp = session.get(
            ACLED_READ_URL,
            params=params,
            headers=headers,
            timeout=TIMEOUT_SECONDS,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Erreur API ACLED (HTTP {resp.status_code}) page {page} : "
                f"{resp.text[:200]}"
            )
        try:
            payload = resp.json()
        except ValueError as e:
            raise RuntimeError(
                f"Réponse ACLED non-JSON page {page} (premiers 300 chars) : "
                f"{resp.text[:300]} ... [{e}]"
            )

        # ACLED renvoie soit {data: [...]} soit {success, count, data: [...]}
        events = payload.get("data", payload) if isinstance(payload, dict) else payload
        if not isinstance(events, list):
            raise RuntimeError(
                f"Format inattendu page {page} : {type(events).__name__}"
            )

        all_events.extend(events)
        print(
            f"    page {page} : {len(events)} événements (cumul {len(all_events)})"
        )

        if len(events) < PAGE_SIZE:
            break
        page += 1
        if page > 200:  # Garde-fou : 200 pages × 5000 = 1M events
            print("    ARRÊT garde-fou : >200 pages atteintes.")
            break

    return all_events


def normalize_event(raw: dict) -> Optional[dict]:
    """Transforme un événement brut ACLED en Feature GeoJSON minifiée.
    Retourne None si l'événement n'est pas géolocalisable."""
    try:
        lat = float(raw.get("latitude"))
        lng = float(raw.get("longitude"))
    except (TypeError, ValueError):
        return None
    if lat == 0 and lng == 0:
        return None  # données suspectes

    fatalities = raw.get("fatalities")
    try:
        fatalities_int = int(fatalities) if fatalities is not None else 0
    except (TypeError, ValueError):
        fatalities_int = 0

    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [round(lng, 3), round(lat, 3)],
        },
        "properties": {
            "d": raw.get("event_date"),
            "t": raw.get("event_type"),
            "st": raw.get("sub_event_type"),
            "c": raw.get("country"),
            "iso": raw.get("iso") or raw.get("iso3"),
            "loc": raw.get("location"),
            "f": fatalities_int,
        },
    }


def compute_aggregates(events: list[dict], today: datetime) -> dict:
    """Calcule les agrégats par pays × fenêtre temporelle (7/30/90j) × catégorie."""
    windows = {"7d": 7, "30d": 30, "90d": 90}
    by_country: dict[str, dict] = {}
    totals: dict[str, dict] = {
        k: {"events": 0, "fatalities": 0, "countries": set()} for k in windows
    }

    for feat in events:
        props = feat["properties"]
        country = props.get("c") or "Unknown"
        event_type = props.get("t") or "Unknown"
        fatalities = props.get("f", 0)
        date_str = props.get("d")
        if not date_str:
            continue
        try:
            event_date = datetime.fromisoformat(date_str)
        except ValueError:
            continue
        days_ago = (today - event_date).days

        if country not in by_country:
            by_country[country] = {
                "iso3": props.get("iso"),
                "windows": {
                    k: {"events": 0, "fatalities": 0, "by_type": defaultdict(int)}
                    for k in windows
                },
            }

        for window_key, window_days in windows.items():
            if days_ago <= window_days:
                by_country[country]["windows"][window_key]["events"] += 1
                by_country[country]["windows"][window_key]["fatalities"] += fatalities
                by_country[country]["windows"][window_key]["by_type"][event_type] += 1
                totals[window_key]["events"] += 1
                totals[window_key]["fatalities"] += fatalities
                totals[window_key]["countries"].add(country)

    # Convertir les defaultdicts en dict ordinaires et les sets en compteur
    for country, data in by_country.items():
        for win in data["windows"].values():
            win["by_type"] = dict(win["by_type"])

    for win in totals.values():
        win["countries_affected"] = len(win["countries"])
        del win["countries"]

    return {"by_country": by_country, "totals": totals}


def write_outputs(events: list[dict], aggregates: dict, source_meta: dict) -> None:
    """Écrit le GeoJSON minifié et le JSON d'agrégats."""
    CONFLICT_DIR.mkdir(parents=True, exist_ok=True)

    now_utc = datetime.now(timezone.utc).isoformat()
    source_block = {
        "id": SOURCE_ID,
        "name": source_meta.get("short_name", "ACLED"),
        "provider": source_meta.get("provider", "ACLED"),
        "window_days": WINDOW_DAYS,
        "reliability": source_meta.get("reliability"),
        "license": source_meta.get("license"),
        "fetched_at_utc": now_utc,
    }

    events_collection = {
        "type": "FeatureCollection",
        "studio_metadata": {
            "schema_version": "1.0.0",
            "source": source_block,
            "events_count": len(events),
            "event_types_present": sorted({
                f["properties"].get("t") for f in events if f["properties"].get("t")
            }),
        },
        "features": events,
    }

    aggregates_payload = {
        "schema_version": "1.0.0",
        "source": source_block,
        "windows_days": {"7d": 7, "30d": 30, "90d": 90},
        **aggregates,
    }

    # GeoJSON minifié (taille réduite, séparateurs compacts)
    with EVENTS_OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(events_collection, f, ensure_ascii=False, separators=(",", ":"))
    with AGGREGATES_OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(aggregates_payload, f, ensure_ascii=False, indent=2)


def main() -> int:
    force = "--force" in sys.argv[1:]

    print(f"=== Ingestion ACLED — script {SCRIPT_VERSION} ===")

    # 1. Cache de fraîcheur (sauf si --force)
    if cache_is_fresh(force):
        age_hours = (
            datetime.now().timestamp() - EVENTS_OUTPUT.stat().st_mtime
        ) / 3600
        print(
            f"Cache encore frais ({age_hours:.1f} h < {CACHE_TTL_SECONDS // 3600} h). "
            f"Re-téléchargement sauté. Utiliser --force pour ignorer."
        )
        return 0

    # 2. Credentials
    try:
        email, password = load_credentials()
    except EnvironmentError as e:
        print(f"FATAL — {e}", file=sys.stderr)
        return 2

    source_meta = load_source_meta()

    # 3. Login session
    try:
        session = open_session(email, password)
    except (requests.RequestException, RuntimeError) as e:
        print(f"FATAL — {e}", file=sys.stderr)
        return 1

    # 4. Calcul de la fenêtre temporelle
    today = datetime.now(timezone.utc)
    start_date = (today - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    # 5. Téléchargement paginé
    try:
        raw_events = fetch_events_window(session, start_date, end_date)
    except (requests.RequestException, RuntimeError) as e:
        print(f"FATAL — téléchargement : {e}", file=sys.stderr)
        return 1

    print(f"  → {len(raw_events)} événements bruts récupérés. Normalisation ...")

    # 6. Normalisation
    features = []
    skipped = 0
    for raw in raw_events:
        feat = normalize_event(raw)
        if feat is None:
            skipped += 1
        else:
            features.append(feat)

    print(f"  → {len(features)} événements géolocalisés, {skipped} ignorés.")

    # 7. Agrégats
    aggregates = compute_aggregates(features, today)
    print(
        f"  → Agrégats : {len(aggregates['by_country'])} pays affectés (90j), "
        f"{aggregates['totals']['7d']['events']} events 7j, "
        f"{aggregates['totals']['30d']['events']} events 30j, "
        f"{aggregates['totals']['90d']['events']} events 90j"
    )

    # 8. Écriture
    write_outputs(features, aggregates, source_meta)

    events_size_mb = EVENTS_OUTPUT.stat().st_size / (1024 * 1024)
    aggregates_size_kb = AGGREGATES_OUTPUT.stat().st_size / 1024
    print(
        f"\nÉvénements écrits : {EVENTS_OUTPUT.relative_to(ROOT)} "
        f"({events_size_mb:.1f} MB)"
    )
    print(
        f"Agrégats écrits   : {AGGREGATES_OUTPUT.relative_to(ROOT)} "
        f"({aggregates_size_kb:.1f} KB)"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
