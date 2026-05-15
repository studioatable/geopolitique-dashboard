# Changelog

Toutes les évolutions notables du projet sont consignées ici. Versioning [SemVer](https://semver.org/lang/fr/).

Catégories d'entrées : `Ajouté` (Added), `Modifié` (Changed), `Déprécié` (Deprecated), `Retiré` (Removed), `Corrigé` (Fixed), `Sécurité` (Security).

---

## [0.1.0] — 2026-05-15 — Cadrage Phase 2 et bootstrap

### Ajouté

- Structure initiale du dépôt : `ingestion/`, `scripts/`, `data/`, `site/`, `docs/`
- Fichier `README.md` avec présentation projet, périmètre, sources v1.0 et instructions d'installation
- Fichier `.gitignore` Python standard + protection `.env`
- Fichier `.env.example` listant les variables attendues sans valeur
- Licence `LICENSE.md` (PolyForm Noncommercial 1.0.0)

### Notes

- Aucune ingestion fonctionnelle à ce stade — étapes 2 à 5 de la roadmap Phase 2 à venir
- Décisions structurantes (stack, frontières, sources v1.0, hébergement o2switch) consignées dans `decisions_phase_2.md` (dossier parent)
- Charte applicative et registre des 41 sources conservés dans le dossier parent

---

## Prochaines versions prévues (roadmap Phase 2)

- `0.2.0` — Script d'audit URLs (étape 2)
- `0.3.0` — Ingestion AFP RSS (étape 3)
- `0.4.0` — Ingestion SIPRI MILEX (étape 4)
- `0.5.0` — Fond de carte Natural Earth (étape 5)
- `0.6.0` — Première page carte mondiale + flux RSS (étape 6)
- `0.7.0` — Déploiement sur `geopolitique.studioatable.fr` (étape 7)
- `0.8.0` — Cron serveur SAT actif (étape 8)
- `0.9.0` — Ingestion ACLED + couche événements (étape 9)
- `1.0.0` — Tests expert hostile + audit IA tierce + publication (étape 10)
- `1.1.0` — Ajout couche frontières ONU commutable
- `1.2.0` — Ajout couche frontières "contrôle effectif"
