# Sources à intégrer ultérieurement

*Document de travail — liste des sources fiables proposées mais non encore qualifiées formellement dans `sources_geopolitiques.json`. Chaque source listée ici sera transformée en fiche JSON complète au moment où elle sera effectivement intégrée à une release (étape 9 et au-delà).*

*Dernière mise à jour : 2026-05-15*

---

## Sources retenues — à qualifier au moment de l'intégration

### Priorité haute

**PRIO — Peace Research Institute Oslo**

- URL : https://www.prio.org/Data/
- Type : Institut de recherche académique (Norvège, fondé 1959)
- Note charte estimée : ★★★★★ (académique peer-reviewed, méthodologie publique)
- Catégorie : `conflict`
- Format : CSV, Excel
- Accès : libre
- Motif d'intégration : co-producteur du *PRIO/UCDP Armed Conflict Dataset*. Standard académique. Complète UCDP avec dimensions historiques et thématiques (battle deaths, cessation hostilities, etc.).
- Cible release : v1.1.0 ou v1.2.0

**UN News (flux RSS officiel ONU)**

- URL : https://news.un.org/fr/feed/rss/1
- Type : Service de presse onusien officiel
- Note charte estimée : ★★★★ (institution multilatérale, communication officielle)
- Catégorie : `news`
- Format : RSS, multilingue (FR, EN, ES, AR, ZH, RU)
- Accès : libre
- Motif d'intégration : complément francophone institutionnel à France 24. Couvre les angles ONU (CSNU, agences spécialisées, opérations de maintien de la paix). Charte respectée (recherche active de sources francophones et européennes/internationales).
- Cible release : v1.1.0

### Priorité moyenne

**Correlates of War (COW)**

- URL : http://www.correlatesofwar.org/data-sets
- Type : Projet académique (Penn State University, fondé 1963)
- Note charte estimée : ★★★★★ (standard académique science politique)
- Catégorie : `conflict`, sous-catégorie historique
- Format : CSV, Excel
- Accès : libre
- Motif d'intégration : profondeur historique exceptionnelle (1816-présent). Utile uniquement si l'axe "vue historique des conflits" devient un axe de différenciation du dashboard. À reconsidérer en v2.
- Cible release : v2.0+ (à valider stratégiquement)

**OCDE Newsroom RSS**

- URL : https://www.oecd.org/newsroom/rss/
- Type : Service communication OCDE
- Note charte estimée : ★★★★ (institution multilatérale, communiqués officiels)
- Catégorie : `news`
- Format : RSS, FR et EN
- Accès : libre
- Motif d'intégration : suivi des publications et positions OCDE sur les pays développés. Utile pour la dimension économie/gouvernance.
- Cible release : v1.2.0 ou v2.0

### Priorité basse

**UN Data (data.un.org)**

- URL : https://data.un.org/
- Type : Méta-portail agrégateur de données ONU
- Note charte estimée : ★★★★ (institution, agrégateur)
- Catégorie : `demographics` ou `economy`
- Format : CSV, Excel
- Accès : libre
- Motif d'intégration : utile comme **catalogue de découverte** pour identifier de nouvelles sources ONU à intégrer, plutôt que comme source primaire (qui doublonne UN WPP et World Bank déjà au registre). Référence documentaire, pas source d'ingestion.
- Cible release : non prévue (à utiliser pour découverte manuelle)

---

## Sources écartées avec motif

**Banque mondiale Blogs (https://www.worldbank.org/en/news/feed)**

- Motif : redondant avec la source `worldbank` déjà au registre (qui couvre l'API de données). Le flux RSS Blogs apporte du commentaire institutionnel, peu utile pour un dashboard data-viz.
- Statut : non intégré.

**FAO Statistics (http://www.fao.org/statistics/en/)**

- Motif : hors périmètre stratégique du dashboard géopolitique actuel (axé conflits, défense, démographie, sanctions, gouvernance). À reconsidérer uniquement si l'axe "sécurité alimentaire" devient un thème prioritaire.
- Statut : non intégré.

---

## Procédure d'intégration

Quand une source de cette liste est mobilisée pour une release :

1. Créer la fiche complète dans `sources_geopolitiques.json` (dossier parent) selon le schéma documenté (§ schema du JSON).
2. Synchroniser dans `data/registry/sources.json` (repo).
3. Passer les 6 critères de qualification de la charte (§ III) — type, indépendance, méthodologie publique, primaire/secondaire, antériorité, reproductibilité — et inscrire la note finale d'étoiles avec son justificatif dans `reliability_note`.
4. Bumper la version `$schema_version` du registre uniquement si le schéma change (par défaut : non).
5. Mettre à jour `last_updated` du registre.
6. Ajouter une entrée dans `CHANGELOG.md` (`### Modifié` — ajout de N source(s) au registre).
7. Bumper la release en `minor` (ajout de source = minor selon charte § VIII).
