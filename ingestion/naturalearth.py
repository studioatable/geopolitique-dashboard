#!/usr/bin/env python3
"""
naturalearth.py — Préparation du fond de carte mondial
=======================================================

Télécharge le GeoJSON Admin 0 (frontières des pays) à la résolution 1:110m
depuis le repo nvkelso/natural-earth-vector, simplifie les propriétés (on ne
garde que ce dont la carte aura besoin), et marque les territoires disputés
conformément à la charte applicative (§ I.2 Neutralité cartographique).

Choix de résolution :
    - 110m (1:110 millions) : ~600 Ko, ~177 features. Idéal pour vue mondiale.
    - 50m et 10m disponibles pour zooms régionaux ultérieurs (étape 9+).

Convention frontières (v1.0) :
    - Natural Earth par défaut, marqueurs sur les territoires disputés.
    - Couches commutables ONU strict / contrôle effectif reportées v1.1/v1.2.

Sorties :
    - data/raw/naturalearth-countries-110m.geojson (brut, indenté)
    - site/data/world.geojson (minifié pour le front, propriétés réduites)

Usage :
    python ingestion/naturalearth.py

Code de sortie :
    0 — préparation réussie
    1 — erreur réseau ou parsing

Studio à Table — geopolitique-dashboard
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

SCRIPT_VERSION = "0.5.0"
SOURCE_ID = "naturalearth"
TIMEOUT_SECONDS = 60
USER_AGENT = (
    f"Studio-a-Table-Geopolitique-Ingest/{SCRIPT_VERSION} "
    "(+https://studioatable.fr)"
)

GEOJSON_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_110m_admin_0_countries.geojson"
)

# Propriétés à conserver dans le GeoJSON minifié servi au front.
# Tout le reste (gdp_md_est, pop_est, mapcolor*, scalerank, etc.) est retiré
# pour réduire la taille et exposer un schéma propre à l'application.
PROPERTIES_TO_KEEP = [
    "iso_a3",       # code ISO 3166-1 alpha-3 (ex. FRA, USA, CHN)
    "name",         # nom usuel anglais (ex. France, United States of America)
    "name_long",    # nom long anglais (ex. French Republic)
    "name_fr",      # nom français (Natural Earth fournit name_fr quand dispo)
    "continent",    # ex. Europe, Asia
    "subregion",    # ex. Western Europe
]

# Territoires marqués comme disputés sur la carte (cf. charte § I.2).
# Clé : nom anglais Natural Earth ; valeur : note explicative.
# Les noms exacts sont vérifiés au runtime contre les features réelles ;
# une note est ajoutée pour ceux qui ne sont pas trouvés (Crimée, Cachemire
# qui n'apparaissent pas comme features distinctes à la résolution 110m).
DISPUTED_TERRITORIES = {
    "W. Sahara": (
        "Sahara occidental — territoire non autonome inscrit sur la liste "
        "de l'ONU depuis 1963. Statut juridique non résolu : revendication "
        "du Maroc, autodétermination réclamée par le Front Polisario."
    ),
    "Western Sahara": (
        "Sahara occidental — territoire non autonome inscrit sur la liste "
        "de l'ONU depuis 1963. Statut juridique non résolu : revendication "
        "du Maroc, autodétermination réclamée par le Front Polisario."
    ),
    "Taiwan": (
        "Taïwan — île administrée par la République de Chine. Revendiquée "
        "par la République populaire de Chine. Reconnaissance internationale "
        "variable selon les États."
    ),
    "Kosovo": (
        "Kosovo — a déclaré son indépendance en 2008. Reconnaissance partagée "
        "internationalement : environ la moitié des États membres de l'ONU "
        "reconnaissent l'indépendance."
    ),
    "Palestine": (
        "Territoires palestiniens (Cisjordanie, bande de Gaza). État de "
        "Palestine reconnu par 138 États membres de l'ONU. Statut final non "
        "résolu."
    ),
    "Israel": (
        "Israël — État dont les frontières définitives ne sont pas reconnues "
        "internationalement (Jérusalem-Est, plateau du Golan, Cisjordanie). "
        "Limites affichées selon Natural Earth, à compléter par une infobulle "
        "UI pour les zones contestées."
    ),
}

# Territoires non distinguables à la résolution 110m mais à signaler dans
# l'interface (infobulle UI sur la carte du pays-hôte).
RESOLUTION_LIMITATIONS = [
    "Crimée : annexée par la Russie en 2014, n'apparaît pas comme feature "
    "distincte à la résolution 1:110m. Infobulle UI requise sur la carte "
    "Ukraine/Russie en étape 6.",
    "Cachemire : zone disputée entre l'Inde, le Pakistan et la Chine, "
    "non distinguée à la résolution 1:110m. Infobulle UI requise.",
]

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "data" / "registry" / "sources.json"
RAW_DIR = ROOT / "data" / "raw"
SITE_DATA_DIR = ROOT / "site" / "data"
RAW_OUTPUT = RAW_DIR / "naturalearth-countries-110m.geojson"
SITE_OUTPUT = SITE_DATA_DIR / "world.geojson"


def load_source_meta() -> dict:
    """Charge la fiche Natural Earth du registre local."""
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"Registre absent : {REGISTRY_PATH}\n"
            "Copier sources_geopolitiques.json depuis le dossier parent."
        )
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        registry = json.load(f)
    for s in registry.get("sources", []):
        if s.get("id") == SOURCE_ID:
            return s
    raise KeyError(f"Source {SOURCE_ID} absente du registre.")


def fetch_geojson(url: str) -> bytes:
    """Télécharge le GeoJSON Natural Earth."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json, application/json;q=0.9, */*;q=0.8"}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.content


def pick_property(props: dict, candidates: list[str]) -> Optional[str]:
    """Cherche la première propriété disponible (case-insensitive) parmi
    les candidats. Natural Earth utilise selon les versions ADMIN, NAME,
    name, sov_a3, etc."""
    lc_props = {k.lower(): v for k, v in props.items()}
    for candidate in candidates:
        if candidate.lower() in lc_props:
            value = lc_props[candidate.lower()]
            if value not in (None, "", "-99"):
                return value
    return None


def normalize_properties(props: dict) -> dict:
    """Réduit les propriétés à celles utiles au front, en absorbant les
    variations de casse de Natural Earth."""
    return {
        "iso_a3": pick_property(props, ["iso_a3", "adm0_a3", "iso_a3_eh"]),
        "name": pick_property(props, ["name", "admin", "name_long"]),
        "name_long": pick_property(props, ["name_long", "formal_en"]),
        "name_fr": pick_property(props, ["name_fr"]),
        "continent": pick_property(props, ["continent"]),
        "subregion": pick_property(props, ["subregion"]),
    }


def mark_disputed(name_en: Optional[str]) -> tuple[bool, Optional[str]]:
    """Retourne (disputed, dispute_note) pour un nom donné."""
    if name_en and name_en in DISPUTED_TERRITORIES:
        return True, DISPUTED_TERRITORIES[name_en]
    return False, None


def simplify_features(features: list[dict]) -> tuple[list[dict], list[str]]:
    """Renvoie (features simplifiées, liste des noms trouvés disputés)."""
    simplified = []
    found_disputed: list[str] = []
    for feat in features:
        original_props = feat.get("properties", {})
        new_props = normalize_properties(original_props)

        # Détection des territoires disputés sur le nom anglais
        disputed, note = mark_disputed(new_props.get("name"))
        new_props["disputed"] = disputed
        if disputed:
            new_props["dispute_note"] = note
            found_disputed.append(new_props["name"])

        simplified.append(
            {
                "type": "Feature",
                "properties": new_props,
                "geometry": feat.get("geometry"),
            }
        )
    return simplified, found_disputed


def write_outputs(
    raw_bytes: bytes,
    site_collection: dict,
    raw_collection: dict,
) -> None:
    """Écrit le brut indenté (debug) et la version minifiée pour le front."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Brut indenté = la version d'origine telle que téléchargée (utile pour
    # debug et traçabilité Git). On ne réécrit pas le brut original pour
    # préserver intégralement le contenu Natural Earth.
    RAW_OUTPUT.write_bytes(raw_bytes)

    # Site : minifié, propriétés simplifiées, métadonnées Studio à Table.
    with SITE_OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(site_collection, f, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    print(f"=== Préparation fond de carte Natural Earth — script {SCRIPT_VERSION} ===")

    try:
        source_meta = load_source_meta()
    except (FileNotFoundError, KeyError) as e:
        print(f"FATAL — {e}", file=sys.stderr)
        return 2

    print(f"Fichier ciblé : {GEOJSON_URL}")

    try:
        raw_bytes = fetch_geojson(GEOJSON_URL)
    except requests.RequestException as e:
        print(f"ERREUR réseau : {e.__class__.__name__} — {e}", file=sys.stderr)
        return 1

    print(f"GeoJSON téléchargé : {len(raw_bytes):,} octets")

    try:
        raw_collection = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"ERREUR parsing JSON : {e}", file=sys.stderr)
        return 1

    features = raw_collection.get("features", [])
    print(f"Features extraites : {len(features)}")

    simplified_features, found_disputed = simplify_features(features)

    now_utc = datetime.now(timezone.utc).isoformat()

    site_collection = {
        "type": "FeatureCollection",
        "name": "world_countries_110m",
        "studio_metadata": {
            "schema_version": "1.0.0",
            "source": {
                "id": SOURCE_ID,
                "name": source_meta.get("short_name", "Natural Earth"),
                "provider": source_meta.get("provider", "Natural Earth"),
                "scale": "1:110m",
                "url": GEOJSON_URL,
                "license": source_meta.get("license", "Public Domain"),
            },
            "fetched_at_utc": now_utc,
            "ingestion_script": "ingestion/naturalearth.py",
            "script_version": SCRIPT_VERSION,
            "convention": "Natural Earth par défaut (v1.0). Couches ONU et contrôle effectif reportées en v1.1/v1.2.",
            "disputed_marked": sorted(set(found_disputed)),
            "resolution_limitations": RESOLUTION_LIMITATIONS,
        },
        "features": simplified_features,
    }

    write_outputs(raw_bytes, site_collection, raw_collection)

    print(f"Territoires disputés marqués : {sorted(set(found_disputed))}")
    print(f"Limitations de résolution signalées : {len(RESOLUTION_LIMITATIONS)}")
    print(f"\nBrut écrit : {RAW_OUTPUT.relative_to(ROOT)} ({RAW_OUTPUT.stat().st_size:,} octets)")
    print(f"Site écrit : {SITE_OUTPUT.relative_to(ROOT)} ({SITE_OUTPUT.stat().st_size:,} octets)")

    # Liste des territoires attendus mais non trouvés à la résolution 110m
    expected = set(DISPUTED_TERRITORIES.keys())
    not_found = expected - set(found_disputed)
    if not_found:
        print(f"\nÀ noter — territoires attendus non trouvés dans Natural Earth 110m : {sorted(not_found)}")
        print("  (Probable : variations de nom ou résolution insuffisante. À investiguer si besoin.)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
