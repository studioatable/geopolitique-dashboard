#!/usr/bin/env python3
"""
encode_logos.py — Encodage base64 des logos SAT pour intégration HTML
======================================================================

Lit `logo-blanc-complet.png` (fond sombre) et `logo-150.png` (fond clair)
depuis le dossier parent du projet (`../`), les encode en base64, et écrit
le fragment HTML à substituer dans `site/index.html` (ou dans un futur
include).

Conforme à la consigne SAT : « TOUJOURS embarquer en base64, jamais via
URL WordPress (hotlink protection studioatable.fr) ».

Usage :
    python scripts/encode_logos.py

Sortie :
    site/_logos.html — fragment HTML à intégrer manuellement dans index.html
    (remplace le SVG placeholder dans <header class="app-header">).

Studio à Table — geopolitique-dashboard
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT_PARENT = ROOT.parent  # le dossier "geopolitique"

LOGO_DARK = PROJECT_PARENT / "logo-blanc-complet.png"  # pour fond sombre
LOGO_LIGHT = PROJECT_PARENT / "logo-150.png"           # pour fond clair
OUTPUT = ROOT / "site" / "_logos.html"


def to_data_uri(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Logo absent : {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def main() -> int:
    try:
        dark_uri = to_data_uri(LOGO_DARK)
        light_uri = to_data_uri(LOGO_LIGHT)
    except FileNotFoundError as e:
        print(f"FATAL — {e}", file=sys.stderr)
        return 1

    dark_size_kb = (LOGO_DARK.stat().st_size + 1023) // 1024
    light_size_kb = (LOGO_LIGHT.stat().st_size + 1023) // 1024

    print(f"Logo fond sombre : {LOGO_DARK.name} ({dark_size_kb} Ko)")
    print(f"Logo fond clair  : {LOGO_LIGHT.name} ({light_size_kb} Ko)")
    print()

    fragment = f"""<!-- Fragment généré par scripts/encode_logos.py — à coller dans index.html
     pour remplacer le SVG placeholder. -->

<!-- Logo header (fond bleu deep) : -->
<img class="logo-header" src="{dark_uri}" alt="Studio à Table" width="180" height="40" />

<!-- Si besoin d'un logo sur fond clair (footer, page méthodologie, etc.) : -->
<img class="logo-footer" src="{light_uri}" alt="Studio à Table" width="120" height="40" />
"""

    OUTPUT.write_text(fragment, encoding="utf-8")
    print(f"Fragment écrit : {OUTPUT.relative_to(ROOT)}")
    print()
    print("Étape suivante : ouvre site/index.html et remplace le bloc")
    print("<svg class=\"logo-placeholder\" ...> ... </svg> par le contenu de")
    print(f"{OUTPUT.relative_to(ROOT)} (le bloc <img class=\"logo-header\" ...>).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
