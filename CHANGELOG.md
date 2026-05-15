# Changelog

Toutes les évolutions notables du projet sont consignées ici. Versioning [SemVer](https://semver.org/lang/fr/).

Catégories d'entrées : `Ajouté` (Added), `Modifié` (Changed), `Déprécié` (Deprecated), `Retiré` (Removed), `Corrigé` (Fixed), `Sécurité` (Security).

---

## [0.2.0] — 2026-05-15 — Script d'audit des sources (étape 2)

### Ajouté

- `scripts/audit_sources.py` — vérifie l'accessibilité HTTP des sources v1.0. Sortie JSON horodatée dans `data/audit/`.
- `requirements.txt` — dépendance unique `requests`.
- `data/registry/sources.json` — copie locale du registre des 41 sources qualifiées (source de vérité maître dans le dossier parent du projet).
- `data/audit/audit_2026-05-15T141719Z.json` — premier rapport d'audit (avec anomalies détectées).

### Modifié

- Périmètre des sources actives v1.0 ajusté **après audit** (le premier audit du 15/05/2026 a détecté 2 anomalies utiles) :
  - **AFP RSS retiré** : l'URL inscrite au registre est une page descriptive (HTTP 404). Remplacé par **France 24 RSS**, source ★★★ francophone également présente au registre.
  - **ACLED reporté à l'étape 9** : `ConnectionError` sur l'endpoint API, à investiguer lors de la demande de clé API. Sources actives v1.0 = SIPRI MILEX + France 24 RSS + Natural Earth.

### Documentation

- `docs/sources_a_integrer.md` — liste de 5 sources retenues pour intégration ultérieure (PRIO, UN News, Correlates of War, OCDE Newsroom RSS, UN Data) + 2 sources écartées avec motif. Pas de fiches JSON créées tant qu'une release ne les active pas, conformément au principe de sobriété (pas de fiches dormantes).

### Notes

- L'audit valide concrètement sa raison d'être : 2 anomalies détectées avant codage d'ingestion.
- Le script accepte HTTP 401/403 pour les sources avec authentification requise (mécanique conservée pour future ré-intégration ACLED).
- Code de sortie 0 si toutes les sources OK ou OK_auth_required, 1 sinon.
- Conforme à l'étape 1 du protocole de validation 5 étapes de la charte applicative.

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
