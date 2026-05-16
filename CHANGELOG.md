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

## [0.6.2] — 2026-05-15 — Lisibilité des labels au zoom + fix unité % PIB

### Corrigé

- **Unité `% du PIB`** : SIPRI stocke "Share of GDP" comme ratio décimal (0,0194). Le JSON normalisé renvoyait donc `0,02 %` pour la France au lieu de `1,94 %`. Correction en amont (ingestion) via un nouveau paramètre `value_multiplier` dans `SHEET_TARGETS` du script `ingestion/sipri_milex.py`. Le JSON et l'affichage portent désormais des pourcentages humains.

### Ajouté

- **Lisibilité des étiquettes au zoom** : taille de police adaptative (9 px à zoom 1, 14 px à zoom 5+) ET filtrage par importance Natural Earth (`labelrank`). Au zoom mondial, seuls les ~20 pays majeurs portent une étiquette ; au zoom continental, ~50 ; au zoom régional, tous. Évite le chevauchement à l'ouverture du dashboard.
- Propriété `labelrank` désormais conservée dans `site/data/world.geojson` (cf. mise à jour `ingestion/naturalearth.py`).
- Fonction utilitaire `pick_numeric()` dans `ingestion/naturalearth.py` pour récupérer les valeurs numériques Natural Earth en gérant correctement la valeur `0`.

---

## [0.6.1] — 2026-05-15 — Correctifs UX (EUR, RSS pays, labels, About)

### Ajouté

- **Conversion EUR** affichée à côté de USD dans le tooltip SIPRI USD constants (taux moyen 2024 BCE = 0,924 EUR/USD). Note méthodologique dans `about.html`.
- **Étiquettes des pays** affichées directement sur la carte via markers HTML positionnés au centroïde de chaque polygone Natural Earth. Markers grisés en italique rouge pour les territoires disputés.
- **Filtre RSS par pays** : un clic sur un pays filtre les dépêches France 24 dont le titre ou résumé contient le nom du pays (FR ou EN) ou un alias enrichi (Moscou, Poutine, Téhéran, etc., pour ~20 pays clés). Lien "tout afficher" pour annuler le filtre. Clic dans l'océan = retour aux 25 dernières dépêches globales.
- **Page `about.html`** dédiée méthodologie, sources, convention cartographique, conversion EUR, note de transparence et licence. Lien depuis le footer minimisé.
- **Menu de navigation** dans le header : `Carte · Conflits (à venir v0.7.0) · À propos`.
- **Traductions FR** des continents Natural Earth (Africa → Afrique, etc.) et des sous-régions (Western Europe → Europe de l'Ouest, etc.). Tooltip affiche désormais "France · Europe · Europe de l'Ouest" plutôt que "France · Europe · Western Europe".
- Table d'alias `COUNTRY_NAME_FR` côté JS pour traduire ~80 noms de pays principaux quand Natural Earth ne fournit pas `name_fr`.

### Modifié

- **Footer minimisé** : copyright + version + lien "À propos & méthodologie" + lien `studioatable.fr`. Tout le contenu méthodologique migré vers `about.html`. La carte gagne ~120 pixels verticaux.
- `.env.example` : `ACLED_API_KEY` retiré (ACLED a migré vers authentification de session Drupal), remplacé par `ACLED_EMAIL` + `ACLED_PASSWORD`.

### Notes

- Performance markers HTML pour les 177 pays Natural Earth 110m : impact négligeable. Si bascule future vers 1:10m (~5000 features), prévoir une couche `symbol` MapLibre avec glyphs CDN.
- Le clic sur l'océan ferme le tooltip ET le filtre RSS — cohérent avec une logique "désélection".

---

## [0.6.0] — 2026-05-15 — Première page carte mondiale + RSS (étape 6)

### Ajouté

- `site/index.html` — structure de la page (header SAT, sélecteur d'indicateur, conteneur MapLibre, sidebar RSS, footer transparence).
- `site/style.css` — feuille de style alignée sur la palette SAT (variables CSS de la charte), typographie Lora + DM Sans via Google Fonts, layout grid carte+sidebar fixe.
- `site/app.js` — initialisation MapLibre GL JS, chargement parallèle des 3 sources (Natural Earth, SIPRI, France 24 RSS), jointure SIPRI↔Natural Earth par nom de pays + table d'alias minimale, sélecteur 3 modes (aucun / USD constants / % PIB), tooltip flottant au clic avec note de territoire disputé si applicable, sidebar RSS (top 25 dépêches).
- `scripts/encode_logos.py` — utilitaire pour encoder les logos SAT (`logo-blanc-complet.png`, `logo-150.png`) en base64 et générer le fragment HTML à substituer dans `index.html`. Logos non encore intégrés (sandbox Claude indisponible) — placeholder SVG en attendant.

### Choix techniques

- **MapLibre GL JS 4.7.1** via CDN unpkg. Pas de fonds de carte externes (tuiles satellites/OSM/Mapbox) — uniquement les polygones Natural Earth en local. Projection Mercator par défaut.
- **Style MapLibre minimaliste** défini en pur JSON, 5 couches : background + countries-fill (choroplèthe) + countries-border + countries-disputed (bordure rouge SAT pointillée) + countries-hover.
- **Joining SIPRI↔Natural Earth par nom anglais**, avec table d'alias `COUNTRY_NAME_ALIASES` (USA, Russia, Czechia, Türkiye, Côte d'Ivoire, etc.). Les pays non matchés sont loggés en console pour traçabilité (méthodologie charte § II.6).
- **Sélecteur 3 modes** : "Aucun" par défaut (frontières seules, conformément au choix utilisateur "carte neutre au départ"), "Dépenses militaires USD", "% du PIB". Légende dynamique en bas à gauche.
- **Tooltip au clic** (pas au hover) : 280px max, position adaptative, badge "Statut disputé" en bordure rouge si applicable, source en bas de tooltip.
- **Logo placeholder SVG** : texte stylisé Lora + soulignement cyan, à remplacer par les vrais logos PNG en base64 via `scripts/encode_logos.py`.

### Notes

- Indexation `noindex, nofollow` dans le `<head>` pour ne pas exposer le MVP aux moteurs avant validation finale (étape 10).
- Note de transparence applicative inscrite dans le footer, conforme à la charte § XIII.
- Convention cartographique v1.0 (Natural Earth + marqueurs disputés) explicite dans le footer.

---

## [0.5.0] — 2026-05-15 — Fond de carte Natural Earth (étape 5)

### Ajouté

- `ingestion/naturalearth.py` — module de préparation du fond de carte mondial. Télécharge le GeoJSON Admin 0 1:110m depuis le repo `nvkelso/natural-earth-vector`, simplifie les propriétés à `iso_a3`, `name`, `name_long`, `name_fr`, `continent`, `subregion`, et marque les territoires disputés selon la charte applicative.
- Sortie principale : `site/data/world.geojson` (minifié, propriétés réduites, prêt pour MapLibre GL JS en étape 6).
- Brut conservé : `data/raw/naturalearth-countries-110m.geojson` (intégral, indenté côté Natural Earth).

### Choix techniques

- **Téléchargement direct du GeoJSON** depuis le repo officiel `nvkelso/natural-earth-vector` plutôt que du Shapefile, pour éviter d'ajouter `pyshp` ou `geopandas` aux dépendances. Sobre et pertinent vu que `nvkelso` est le mainteneur officiel.
- **Résolution 1:110m** retenue pour la vue mondiale (~600 Ko, ~177 features). Les résolutions 50m et 10m sont disponibles si besoin de zooms régionaux en v1.x+.
- **Marquage des territoires disputés** : Western Sahara, Taiwan, Kosovo, Palestine, Israël avec note explicative neutre (statut ONU + positions divergentes). Conforme à la charte § I.2 (Neutralité cartographique assumée mais documentée).
- **Limitations de résolution signalées** dans `studio_metadata.resolution_limitations` : Crimée et Cachemire ne sont pas des features distinctes à 1:110m, infobulle UI à prévoir en étape 6.

### Notes

- Aucune nouvelle dépendance Python ajoutée. Le module utilise uniquement `requests` (déjà présent) + `json` et `pathlib` (stdlib).
- Convention v1.0 explicitement inscrite dans les métadonnées du GeoJSON pour traçabilité par le front.

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

- `0.7.0` — Déploiement sur `geopolitique.studioatable.fr` (étape 7)
- `0.8.0` — Cron serveur SAT actif (étape 8)
- `0.9.0` — Ingestion ACLED + couche événements (étape 9)
- `1.0.0` — Tests expert hostile + audit IA tierce + publication (étape 10)
- `1.1.0` — Ajout couche frontières ONU commutable
- `1.2.0` — Ajout couche frontières "contrôle effectif"
