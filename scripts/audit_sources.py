#!/usr/bin/env python3
"""
audit_sources.py — Audit minimal des sources de données v1.0
============================================================

Vérifie pour chaque source ciblée : URL vivante (HTTP 200), content-type,
taille, latence. Pour ACLED, un 401 sans clé est attendu et considéré OK.
Sortie : data/audit/audit_YYYY-MM-DDTHHMMSSZ.json (horodaté UTC).

Conforme à l'étape 1 du protocole de validation 5 étapes de la charte
applicative (vérification de l'accès avant intégration).

Usage :
    python scripts/audit_sources.py

Code de sortie :
    0 — toutes les sources OK ou OK auth requise
    1 — au moins une source en erreur

Studio à Table — geopolitique-dashboard v0.2.0
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

SCRIPT_VERSION = "0.2.0"
TIMEOUT_SECONDS = 30
USER_AGENT = (
    "Studio-a-Table-Geopolitique-Audit/0.2.0 "
    "(+https://studioatable.fr)"
)

# Identifiants des sources auditées en v1.0 (cf. decisions_phase_2.md § 5)
#
# Note de versioning audit (2026-05-15) :
#   - 'acled' reporté à l'étape 9 de la roadmap : nécessite une clé API et
#     l'endpoint api.acleddata.com a renvoyé une erreur de connexion à l'audit.
#     Investigation et bascule prévues lors de l'intégration ACLED.
#   - 'afp_rss' retiré : l'URL inscrite au registre est une page descriptive
#     (HTTP 404 sur audit), pas un flux RSS actif. Remplacé par 'france24_rss'
#     (★★★, francophone, charte respectée — recherche active de sources FR).
SOURCES_V1 = ["sipri_milex", "france24_rss", "naturalearth"]

# Pour ces sources, un code 401/403 est attendu si la clé n'est pas fournie
# et doit être considéré comme un succès d'accessibilité de l'endpoint.
# (Conservé pour future ré-intégration ACLED.)
EXPECT_AUTH = {"acled"}

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "data" / "registry" / "sources.json"
AUDIT_OUTPUT_DIR = ROOT / "data" / "audit"


def load_registry() -> dict:
    """Charge le registre des sources géopolitiques."""
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"Registre absent : {REGISTRY_PATH}\n"
            f"Copier sources_geopolitiques.json depuis le dossier parent."
        )
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_source(registry: dict, source_id: str) -> Optional[dict]:
    """Retourne la fiche d'une source ou None si absente."""
    for s in registry.get("sources", []):
        if s.get("id") == source_id:
            return s
    return None


def pick_url(source: dict) -> Optional[str]:
    """Choisit la meilleure URL à auditer : url_api > url_data > url_home."""
    return source.get("url_api") or source.get("url_data") or source.get("url_home")


def audit_one(source: dict) -> dict:
    """Audite une source. Retourne un dict structuré."""
    url = pick_url(source)
    result = {
        "id": source["id"],
        "name": source.get("short_name", source.get("name", "?")),
        "url_audited": url,
        "method": None,
        "status_code": None,
        "content_type": None,
        "content_length": None,
        "elapsed_ms": None,
        "verdict": "unknown",
        "notes": [],
    }

    if not url:
        result["verdict"] = "no_url"
        result["notes"].append("Aucune URL exploitable dans la fiche.")
        return result

    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    accept_auth_required = source["id"] in EXPECT_AUTH

    try:
        # Tentative HEAD d'abord (économise la bande passante)
        resp = requests.head(
            url,
            headers=headers,
            timeout=TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        method_used = "HEAD"

        # Certains serveurs n'autorisent pas HEAD : fallback GET avec streaming
        if resp.status_code in (405, 403, 501) and not accept_auth_required:
            resp = requests.get(
                url,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
                stream=True,
            )
            method_used = "GET"
            # Lire un petit échantillon pour fermer proprement la connexion
            for _chunk in resp.iter_content(chunk_size=1024):
                break

        content_length_header = resp.headers.get("Content-Length")
        try:
            content_length = (
                int(content_length_header) if content_length_header else None
            )
        except ValueError:
            content_length = None

        result["method"] = method_used
        result["status_code"] = resp.status_code
        result["content_type"] = resp.headers.get("Content-Type")
        result["content_length"] = content_length
        result["elapsed_ms"] = int(resp.elapsed.total_seconds() * 1000)

        if resp.status_code == 200:
            result["verdict"] = "ok"
        elif accept_auth_required and resp.status_code in (401, 403):
            result["verdict"] = "ok_auth_required"
            result["notes"].append(
                "Endpoint répond ; authentification requise (clé API attendue)."
            )
        elif 300 <= resp.status_code < 400:
            result["verdict"] = "warning"
            result["notes"].append(
                f"Redirection non suivie (code {resp.status_code})."
            )
        else:
            result["verdict"] = "warning"
            result["notes"].append(f"Code HTTP inattendu : {resp.status_code}")

    except requests.Timeout:
        result["verdict"] = "error"
        result["notes"].append(f"Timeout après {TIMEOUT_SECONDS}s.")
    except requests.ConnectionError as e:
        result["verdict"] = "error"
        result["notes"].append(f"Erreur de connexion : {e.__class__.__name__}")
    except requests.RequestException as e:
        result["verdict"] = "error"
        result["notes"].append(f"Erreur réseau : {e.__class__.__name__}")

    return result


def main() -> int:
    print(f"=== Audit sources v1.0 — script {SCRIPT_VERSION} ===")
    print(f"Sources ciblées : {', '.join(SOURCES_V1)}\n")

    try:
        registry = load_registry()
    except FileNotFoundError as e:
        print(f"FATAL — {e}", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    timestamp_iso = now.isoformat()
    timestamp_filename = now.strftime("%Y-%m-%dT%H%M%SZ")

    results = []
    for source_id in SOURCES_V1:
        src = get_source(registry, source_id)
        if src is None:
            print(f"  {source_id:<14} → absent du registre")
            results.append(
                {
                    "id": source_id,
                    "verdict": "missing_in_registry",
                    "notes": ["Identifiant absent du registre."],
                }
            )
            continue

        print(f"  {source_id:<14} → ", end="", flush=True)
        r = audit_one(src)
        verdict_label = r["verdict"]
        status_info = (
            f" (HTTP {r['status_code']}, {r['elapsed_ms']} ms)"
            if r["status_code"]
            else ""
        )
        print(f"{verdict_label}{status_info}")
        for note in r["notes"]:
            print(f"      • {note}")
        results.append(r)

    summary = {
        "total": len(results),
        "ok": sum(1 for r in results if r["verdict"].startswith("ok")),
        "warning": sum(1 for r in results if r["verdict"] == "warning"),
        "error": sum(1 for r in results if r["verdict"] == "error"),
        "missing": sum(
            1 for r in results if r["verdict"] == "missing_in_registry"
        ),
    }

    report = {
        "script_version": SCRIPT_VERSION,
        "audit_timestamp_utc": timestamp_iso,
        "registry_schema_version": registry.get("$schema_version"),
        "registry_last_updated": registry.get("last_updated"),
        "sources_audited": SOURCES_V1,
        "results": results,
        "summary": summary,
    }

    AUDIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = AUDIT_OUTPUT_DIR / f"audit_{timestamp_filename}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nRapport écrit : {out_path.relative_to(ROOT)}")
    print(
        f"Synthèse : {summary['ok']} ok, "
        f"{summary['warning']} warning, "
        f"{summary['error']} error, "
        f"{summary['missing']} absent"
    )

    return 0 if summary["error"] == 0 and summary["missing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
