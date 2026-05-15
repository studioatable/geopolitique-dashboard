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

## [0.4.0] — 2026-05-15 — Ingestion SIPRI MILEX (étape 4)

### Ajouté

- `ingestion/sipri_milex.py` — module d'ingestion du fichier XLSX SIPRI MILEX. Télécharge, parse via `openpyxl`, extrait deux indicateurs (USD constants et % du PIB), normalise en JSON multi-indicateurs.
- `openpyxl>=3.1,<4.0` ajouté à `requirements.txt`.
- Sortie : `data/defense/sipri_milex.json` avec structure `{indicators: {milex_constant_usd: {...}, milex_pct_gdp: {...}}}` et données par pays/année.

### Choix techniques

- **URL XLSX hardcodée** en v0.4.0 (révision `SIPRI-Milex-data-1949-2025_v1.2.xlsx`, avril 2026). Évolution prévue v0.4.1 : scraping de la page d'accueil SIPRI pour suivre automatiquement les futures révisions annuelles.
- **Auto-détection de la ligne d'en-tête** par recherche d'au moins 5 années consécutives dans les 20 premières lignes — résiste aux ajustements de mise en forme entre révisions SIPRI.
- **Auto-détection des feuilles cibles** par patterns lower-case (ex. `["constant", "us$"]`), pour absorber les variations de libellés (année de référence USD).
- **Exclusion des agrégats régionaux** (World total, Africa, Asia, etc.) — à intégrer dans un indicateur dédié futur si besoin.
- **Marqueurs de données manquantes** SIPRI (`xxx`, `. .`, `..`) gérés explicitement et exclus de la sortie.

### Notes

- Les noms de pays sont en anglais (libellés SIPRI). Mapping vers codes ISO-3 et noms français prévu en v0.4.x via REST Countries ou un mapping local.
- Le module n'a pas été testé contre le fichier réel côté Claude (sandbox indisponible). Premier run par Yvan : ajustements possibles sur les patterns de feuilles ou les exclusions de lignes selon la structure réelle du fichier.

---

## [0.3.0] — 2026-05-15 — Ingestion France 24 RSS (étape 3)

### Ajouté

- `ingestion/france24.py` — module d'ingestion du flux RSS France 24. Télécharge le XML brut, parse via `feedparser`, normalise en JSON conforme à un schéma commun (id, source, titre, résumé, lien, dates UTC + brut, langue, tags, auteur).
- `feedparser>=6.0,<7.0` ajouté à `requirements.txt` — parser RSS/Atom standard, robuste aux flux légèrement non conformes.
- Schéma de sortie commun documenté dans le script (`schema_version: 1.0.0`), réutilisable pour les futurs modules d'ingestion RSS (UN News, France 24 alternatif, Le Monde, etc.).

### Choix techniques

- **Brut écrasé à chaque exécution** (`data/raw/france24-latest.xml`) plutôt que versionnement horodaté, par sobriété. L'historique est tenu par Git via les commits horarires/quotidiens. Évolution possible en v1.1+ si la traçabilité fine devient utile.
- **JSON normalisé toujours dans `data/rss/france24.json`** (toujours la version la plus récente), pour intégration directe par le frontend en étape 6.
- IDs d'items stables (hash du link/guid) pour permettre dédoublonnage à venir entre exécutions successives.

---

## Prochaines versions prévues (roadmap Phase 2)

- `0.5.0` — Fond de carte Natural Earth (étape 5)
- `0.6.0` — Première page carte mondiale + flux RSS (étape 6)
- `0.7.0` — Déploiement sur `geopolitique.studioatable.fr` (étape 7)
- `0.8.0` — Cron serveur SAT actif (étape 8)
- `0.9.0` — Ingestion ACLED + couche événements (étape 9)
- `1.0.0` — Tests expert hostile + audit IA tierce + publication (étape 10)
- `1.1.0` — Ajout couche frontières ONU commutable
- `1.2.0` — Ajout couche frontières "contrôle effectif"
