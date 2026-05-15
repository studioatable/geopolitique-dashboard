#!/usr/bin/env python3
"""
france24.py — Ingestion du flux RSS France 24
==============================================

Télécharge le flux RSS France 24, parse les items, normalise en JSON
conforme à un schéma commun multi-source.

Stratégie d'archivage (MVP) :
    - Le XML brut le plus récent est écrit dans data/raw/france24-latest.xml
      (écrasé à chaque exécution — l'historique est tenu par Git via les commits).
    - Le JSON normalisé est écrit dans data/rss/france24.json (toujours le plus récent).
    - Évolution possible (v1.1+) : versionnement horodaté du brut si la traçabilité
      au-delà du grain Git devient utile.

Usage :
    python ingestion/france24.py

Code de sortie :
    0 — ingestion réussie
    1 — erreur réseau ou parsing

Studio à Table — geopolitique-dashboard
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import feedparser
import requests

SCRIPT_VERSION = "0.3.0"
SOURCE_ID = "france24_rss"
TIMEOUT_SECONDS = 30
USER_AGENT = (
    f"Studio-a-Table-Geopolitique-Ingest/{SCRIPT_VERSION} "
    "(+https://studioatable.fr)"
)

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "data" / "registry" / "sources.json"
RAW_DIR = ROOT / "data" / "raw"
RSS_DIR = ROOT / "data" / "rss"
RAW_OUTPUT = RAW_DIR / "france24-latest.xml"
JSON_OUTPUT = RSS_DIR / "france24.json"


def load_source_meta() -> dict:
    """Charge la fiche France 24 depuis le registre local."""
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


def fetch_feed(url: str) -> bytes:
    """Télécharge le XML brut du flux RSS. Lève une exception si erreur réseau."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8"}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.content


def normalize_published(entry: dict) -> tuple[Optional[str], Optional[str]]:
    """Retourne (published_utc_iso, published_raw) pour un item parsé."""
    raw = entry.get("published") or entry.get("updated")
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed is None:
        return None, raw
    try:
        # feedparser donne un time.struct_time en UTC
        dt = datetime(*parsed[:6], tzinfo=timezone.utc)
        return dt.isoformat(), raw
    except (TypeError, ValueError):
        return None, raw


def build_item_id(source_id: str, entry: dict) -> str:
    """ID stable basé sur le lien ou le guid (sinon hash du titre + date)."""
    candidate = entry.get("id") or entry.get("guid") or entry.get("link")
    if not candidate:
        seed = (entry.get("title", "") + (entry.get("published") or "")).encode("utf-8")
        candidate = hashlib.sha1(seed).hexdigest()[:16]
    short = hashlib.sha1(candidate.encode("utf-8")).hexdigest()[:12]
    return f"{source_id}-{short}"


def clean_text(text: Optional[str]) -> Optional[str]:
    """Nettoyage minimal d'un texte issu du flux."""
    if text is None:
        return None
    return " ".join(text.strip().split())


def normalize_entries(parsed_feed, source_meta: dict) -> list[dict]:
    """Transforme les entries feedparser en items normalisés."""
    items = []
    for entry in parsed_feed.entries:
        published_utc, published_raw = normalize_published(entry)
        item = {
            "id": build_item_id(SOURCE_ID, entry),
            "source_id": SOURCE_ID,
            "source_name": source_meta.get("short_name", "France 24"),
            "source_category": source_meta.get("category", "news"),
            "title": clean_text(entry.get("title")),
            "summary": clean_text(entry.get("summary")),
            "link": entry.get("link"),
            "published_utc": published_utc,
            "published_raw": published_raw,
            "language": (
                parsed_feed.feed.get("language")
                or entry.get("language")
                or "fr"
            ),
            "tags": [
                t.get("term") for t in entry.get("tags", []) if t.get("term")
            ],
            "author": clean_text(entry.get("author")),
        }
        items.append(item)
    return items


def write_outputs(raw_xml: bytes, items: list[dict], source_meta: dict, feed_url: str) -> None:
    """Écrit le XML brut et le JSON normalisé."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RSS_DIR.mkdir(parents=True, exist_ok=True)

    RAW_OUTPUT.write_bytes(raw_xml)

    now_utc = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": "1.0.0",
        "ingestion_script": "ingestion/france24.py",
        "script_version": SCRIPT_VERSION,
        "source": {
            "id": SOURCE_ID,
            "name": source_meta.get("short_name", "France 24"),
            "provider": source_meta.get("provider", "France Médias Monde"),
            "category": source_meta.get("category", "news"),
            "feed_url": feed_url,
            "reliability": source_meta.get("reliability"),
            "license": source_meta.get("license"),
        },
        "fetched_at_utc": now_utc,
        "items_count": len(items),
        "items": items,
    }
    with JSON_OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def pick_feed_url(source_meta: dict) -> str:
    """URL du flux RSS — url_data dans le registre (fallback url_home)."""
    url = source_meta.get("url_data") or source_meta.get("url_home")
    if not url:
        raise ValueError("Aucune URL exploitable dans la fiche France 24.")
    return url


def main() -> int:
    print(f"=== Ingestion France 24 RSS — script {SCRIPT_VERSION} ===")

    try:
        source_meta = load_source_meta()
    except (FileNotFoundError, KeyError) as e:
        print(f"FATAL — {e}", file=sys.stderr)
        return 2

    feed_url = pick_feed_url(source_meta)
    print(f"Flux ciblé : {feed_url}")

    try:
        raw_xml = fetch_feed(feed_url)
    except requests.RequestException as e:
        print(f"ERREUR réseau : {e.__class__.__name__} — {e}", file=sys.stderr)
        return 1

    print(f"XML téléchargé : {len(raw_xml)} octets")

    # France 24 sert en UTF-8 mais ne déclare pas toujours le charset dans le
    # header Content-Type. Sans cet indice, feedparser se rabat sur une
    # heuristique qui lit parfois les bytes UTF-8 comme du Latin-1
    # ('é' → 'Ã©'). On lui passe une string décodée explicitement pour court-
    # circuiter ce piège.
    try:
        feed_input = raw_xml.decode("utf-8")
    except UnicodeDecodeError:
        feed_input = raw_xml  # fallback : laisser feedparser détecter

    parsed = feedparser.parse(feed_input)
    if parsed.bozo and not parsed.entries:
        print(
            f"ERREUR parsing — feedparser.bozo={parsed.bozo}, "
            f"raison : {parsed.bozo_exception}",
            file=sys.stderr,
        )
        return 1

    items = normalize_entries(parsed, source_meta)
    print(f"Items extraits : {len(items)}")

    if not items:
        print("ATTENTION : aucun item extrait, mais pas d'erreur de parsing.")
        # On écrit quand même la sortie pour traçabilité

    write_outputs(raw_xml, items, source_meta, feed_url)
    print(f"Brut écrit : {RAW_OUTPUT.relative_to(ROOT)}")
    print(f"JSON écrit : {JSON_OUTPUT.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
