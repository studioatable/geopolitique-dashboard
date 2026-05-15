# Géopolitique Dashboard — Studio à Table

Tableau de bord interactif pour le suivi des conflits, dépenses militaires, actualités et indicateurs géopolitiques. Produit par [Studio à Table](https://studioatable.fr).

**Version courante** : `0.1.0` — cadrage Phase 2, bootstrap du projet.

**URL cible** : [geopolitique.studioatable.fr](https://geopolitique.studioatable.fr) (à venir, déploiement en étape 7 de la roadmap Phase 2).

---

## Périmètre du dépôt

Ce dépôt contient l'intégralité du code et de la donnée normalisée du tableau de bord :

- `ingestion/` — modules Python d'ingestion par source de données
- `scripts/` — scripts utilitaires (audit, vérification, déploiement)
- `data/` — données téléchargées (`raw/`) et normalisées (`rss/`, `defense/`, etc.)
- `site/` — application statique HTML/JS/CSS + fond de carte
- `docs/` — documentation méthodologique, sources, captures

Les documents de cadrage (charte applicative, registre des 41 sources, décisions Phase 2) sont conservés dans le dossier parent du projet et référencés ici pour mémoire.

---

## Sources de données — v1.0 (actives)

| Source | Catégorie | Cadence | Accès |
|---|---|---|---|
| SIPRI MILEX | Dépenses militaires | Annuel | Libre (XLSX) |
| France 24 RSS | Actualités | Temps réel | RSS public |
| Natural Earth | Fond de carte | Statique | Libre |

### Sources reportées

- **ACLED** (Conflits) — intégration prévue à l'étape 9 de la roadmap, après demande de clé API gratuite. Investigation préalable nécessaire (l'audit a relevé un `ConnectionError` sur l'endpoint API public).
- **AFP RSS** — initialement prévue, retirée après audit (URL inscrite au registre = page descriptive, pas un flux). Remplacée par France 24 RSS (★★★, francophone, charte respectée).

Registre complet (41 sources qualifiées) dans `data/registry/sources.json` ou dans le fichier maître `sources_geopolitiques.json` (dossier parent).

---

## Installation locale

```bash
# Cloner le dépôt
git clone https://github.com/studioatable/geopolitique-dashboard.git
cd geopolitique-dashboard

# Environnement Python
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Dépendances (à créer en étape 2 de la roadmap)
pip install -r requirements.txt

# Variables d'environnement
cp .env.example .env
# Éditer .env et renseigner les clés API
```

---

## Licence

Code et données publiés sous **PolyForm Noncommercial 1.0.0**. Voir `LICENSE.md`.

Usage non commercial autorisé avec attribution. Pour tout usage commercial, contacter `contact@studioatable.fr`.

---

## Méthodologie

Le projet respecte une charte applicative en 13 sections (validation croisée des sources, neutralité cartographique documentée, honnêteté épistémique, etc.). Voir le document `charte_application_geopolitique.md` dans le dossier parent.

Chaque donnée affichée porte sa source, sa date de mesure et sa fréquence réelle de mise à jour. Aucune homogénéisation forcée entre sources divergentes.

---

## Statut et roadmap

Voir `CHANGELOG.md` pour l'historique des versions, et `decisions_phase_2.md` (dossier parent) pour la roadmap des 10 étapes de la Phase 2.

---

*Studio à Table — Stratégie de marque et communication — Gers / Toulouse, France*
