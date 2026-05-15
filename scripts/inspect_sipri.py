#!/usr/bin/env python3
"""
inspect_sipri.py — Inspection rapide du JSON SIPRI MILEX
=========================================================

Affiche un récapitulatif lisible du dernier fichier produit par
`ingestion/sipri_milex.py`. Utilitaire de QA, pas un script d'ingestion.

Usage :
    python scripts/inspect_sipri.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "data" / "defense" / "sipri_milex.json"


def main() -> int:
    if not JSON_PATH.exists():
        print(f"FATAL — fichier absent : {JSON_PATH}", file=sys.stderr)
        return 1

    with JSON_PATH.open("r", encoding="utf-8") as f:
        d = json.load(f)

    print(f"=== Inspection SIPRI MILEX — {JSON_PATH.name} ===")
    print(f"Script version : {d.get('script_version')}")
    print(f"Fetched (UTC)  : {d.get('fetched_at_utc')}")
    print(f"XLSX source    : {d['source']['xlsx_url']}")
    print()

    indicators = d.get("indicators", {})
    print(f"Indicateurs : {len(indicators)}")
    for indicator_id, ind in indicators.items():
        print(
            f"  - {indicator_id} : "
            f"{ind['countries_count']} pays, "
            f"{ind['years_min']}-{ind['years_max']}, "
            f"unité = {ind['unit']}"
        )

    print()
    notes = d.get("notes", [])
    if notes:
        print(f"Notes ({len(notes)}) :")
        for n in notes:
            print(f"  ! {n}")
        print()

    # Aperçu France sur l'indicateur principal
    main_id = "milex_constant_usd"
    if main_id in indicators:
        france = indicators[main_id]["data"].get("France", {})
        years = sorted(france.keys())
        print(f"France ({main_id}) : {len(years)} années renseignées")
        if years:
            # Premières et dernières années
            print(f"  premières : {years[0]} = {france[years[0]]}")
            print(f"  dernières : {years[-1]} = {france[years[-1]]}")
        print()

    # Top 10 dépenses 2025 si dispo
    if main_id in indicators:
        data = indicators[main_id]["data"]
        latest = max(
            (y for c in data.values() for y in c.keys()), default=None
        )
        if latest:
            ranking = sorted(
                ((c, v.get(latest)) for c, v in data.items() if v.get(latest)),
                key=lambda x: -x[1],
            )[:10]
            print(f"Top 10 dépenses militaires {latest} (USD constants, millions) :")
            for i, (country, value) in enumerate(ranking, 1):
                print(f"  {i:2d}. {country:<30} {value:>15,.0f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
