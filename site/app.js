// =============================================================================
// Géopolitique Dashboard — Studio à Table
// app.js v0.6.0 — initialisation MapLibre, choroplèthes, RSS, tooltip
// =============================================================================
//
// Responsabilités :
//   - Charger les 3 jeux de données (Natural Earth, SIPRI, France 24 RSS)
//   - Initialiser MapLibre avec une source GeoJSON
//   - Joindre les données SIPRI aux features Natural Earth (par nom de pays)
//   - Gérer le sélecteur d'indicateur (3 modes : aucun / USD / % PIB)
//   - Afficher tooltip flottant au clic sur un pays
//   - Afficher le flux RSS dans la sidebar
//
// Architecture v0.6.0 : tout en un seul fichier, IIFE non utilisée car
// servi en site statique simple. Pas de bundler. Code lisible avant tout.
// =============================================================================

'use strict';

// ---------------------------------------------------------------------------
// 0. Constantes et configuration
// ---------------------------------------------------------------------------

const DATA_PATHS = {
  worldGeoJson: 'data/world.geojson',
  sipri: '../data/defense/sipri_milex.json',
  rss: '../data/rss/france24.json',
};

// Année cible pour la choroplèthe (dernière année dispo dans SIPRI)
const TARGET_YEAR = '2025';

// Taux de change moyen EUR/USD 2024 — source BCE (1 USD ≈ 0,924 EUR).
// Conversion à titre indicatif sur des valeurs SIPRI publiées en USD constants 2024.
// Documenté dans about.html.
const EUR_PER_USD_2024 = 0.924;

// Palette SAT pour les choroplèthes (gradient bleus, du clair au profond)
const CHOROPLETH_STOPS_USD = [
  // [valeur en millions USD constants, couleur]
  [0,        '#F3F3F3'],
  [1000,     '#D5EAF7'],
  [5000,     '#B6E1FA'],
  [20000,    '#62D0FF'],
  [50000,    '#40C6FF'],
  [100000,   '#0678B7'],
  [300000,   '#053144'],
];

const CHOROPLETH_STOPS_PCT_GDP = [
  // [valeur en % du PIB, couleur]
  [0,    '#F3F3F3'],
  [0.5,  '#D5EAF7'],
  [1.0,  '#B6E1FA'],
  [2.0,  '#62D0FF'],
  [3.5,  '#40C6FF'],
  [6.0,  '#0678B7'],
  [10.0, '#053144'],
];

const NO_DATA_COLOR = '#E7E2E2';
const COUNTRY_BORDER = '#FFFFFF';
const COUNTRY_BORDER_DISPUTED = '#BC534F';

// Mapping manuel des noms de pays SIPRI → noms Natural Earth quand les noms
// divergent. À enrichir au besoin (la charte recommande la traçabilité de
// ce type d'arbitrage méthodologique). Liste minimale v0.6.0.
const COUNTRY_NAME_ALIASES = {
  // SIPRI → Natural Earth
  'United States of America': ['United States of America', 'United States'],
  'Korea, South': ['South Korea'],
  'Korea, North': ['North Korea'],
  'Iran': ['Iran'],
  'Russia': ['Russia'],
  'Czechia': ['Czech Republic', 'Czechia'],
  'Cabo Verde': ['Cape Verde'],
  'Eswatini': ['eSwatini', 'Swaziland'],
  'Türkiye': ['Turkey'],
  'Viet Nam': ['Vietnam'],
  "Côte d'Ivoire": ['Ivory Coast'],
};

// Traductions FR des continents et sous-régions Natural Earth.
// Utilisées dans le tooltip pour cohérence francophone.
const CONTINENT_FR = {
  'Africa': 'Afrique',
  'Antarctica': 'Antarctique',
  'Asia': 'Asie',
  'Europe': 'Europe',
  'North America': 'Amérique du Nord',
  'Oceania': 'Océanie',
  'Seven seas (open ocean)': 'Océan ouvert',
  'South America': 'Amérique du Sud',
};

const SUBREGION_FR = {
  'Australia and New Zealand': 'Australie et Nouvelle-Zélande',
  'Caribbean': 'Caraïbes',
  'Central America': 'Amérique centrale',
  'Central Asia': 'Asie centrale',
  'Eastern Africa': 'Afrique de l\'Est',
  'Eastern Asia': 'Asie de l\'Est',
  'Eastern Europe': 'Europe de l\'Est',
  'Melanesia': 'Mélanésie',
  'Micronesia': 'Micronésie',
  'Middle Africa': 'Afrique centrale',
  'Northern Africa': 'Afrique du Nord',
  'Northern America': 'Amérique septentrionale',
  'Northern Europe': 'Europe du Nord',
  'Polynesia': 'Polynésie',
  'Seven seas (open ocean)': 'Océan ouvert',
  'South America': 'Amérique du Sud',
  'South-Eastern Asia': 'Asie du Sud-Est',
  'Southern Africa': 'Afrique australe',
  'Southern Asia': 'Asie du Sud',
  'Southern Europe': 'Europe du Sud',
  'Western Africa': 'Afrique de l\'Ouest',
  'Western Asia': 'Asie de l\'Ouest',
  'Western Europe': 'Europe de l\'Ouest',
};

// Alias FR de pays pour enrichir le filtrage RSS et le tooltip quand
// Natural Earth ne fournit pas name_fr. Liste minimale v0.6.1.
const COUNTRY_NAME_FR = {
  'United States of America': 'États-Unis',
  'United States': 'États-Unis',
  'United Kingdom': 'Royaume-Uni',
  'Germany': 'Allemagne',
  'Russia': 'Russie',
  'China': 'Chine',
  'Japan': 'Japon',
  'India': 'Inde',
  'Saudi Arabia': 'Arabie saoudite',
  'Italy': 'Italie',
  'Spain': 'Espagne',
  'Brazil': 'Brésil',
  'South Korea': 'Corée du Sud',
  'North Korea': 'Corée du Nord',
  'Iran': 'Iran',
  'Israel': 'Israël',
  'Egypt': 'Égypte',
  'Turkey': 'Turquie',
  'Greece': 'Grèce',
  'Sweden': 'Suède',
  'Norway': 'Norvège',
  'Finland': 'Finlande',
  'Denmark': 'Danemark',
  'Poland': 'Pologne',
  'Belgium': 'Belgique',
  'Netherlands': 'Pays-Bas',
  'Switzerland': 'Suisse',
  'Austria': 'Autriche',
  'Portugal': 'Portugal',
  'Ireland': 'Irlande',
  'Czech Republic': 'Tchéquie',
  'Czechia': 'Tchéquie',
  'Hungary': 'Hongrie',
  'Romania': 'Roumanie',
  'Bulgaria': 'Bulgarie',
  'Serbia': 'Serbie',
  'Croatia': 'Croatie',
  'Slovakia': 'Slovaquie',
  'Slovenia': 'Slovénie',
  'Ukraine': 'Ukraine',
  'Belarus': 'Biélorussie',
  'Lithuania': 'Lituanie',
  'Latvia': 'Lettonie',
  'Estonia': 'Estonie',
  'Iceland': 'Islande',
  'Mexico': 'Mexique',
  'Canada': 'Canada',
  'Australia': 'Australie',
  'New Zealand': 'Nouvelle-Zélande',
  'Indonesia': 'Indonésie',
  'Thailand': 'Thaïlande',
  'Vietnam': 'Viêt Nam',
  'Philippines': 'Philippines',
  'Malaysia': 'Malaisie',
  'Singapore': 'Singapour',
  'Pakistan': 'Pakistan',
  'Bangladesh': 'Bangladesh',
  'Afghanistan': 'Afghanistan',
  'Syria': 'Syrie',
  'Iraq': 'Irak',
  'Lebanon': 'Liban',
  'Jordan': 'Jordanie',
  'Yemen': 'Yémen',
  'Libya': 'Libye',
  'Algeria': 'Algérie',
  'Morocco': 'Maroc',
  'Tunisia': 'Tunisie',
  'Sudan': 'Soudan',
  'Ethiopia': 'Éthiopie',
  'Kenya': 'Kenya',
  'Nigeria': 'Nigéria',
  'South Africa': 'Afrique du Sud',
  'Democratic Republic of the Congo': 'République démocratique du Congo',
  'Congo': 'Congo',
  'Mali': 'Mali',
  'Senegal': 'Sénégal',
  'Niger': 'Niger',
  'Burkina Faso': 'Burkina Faso',
  'Cameroon': 'Cameroun',
  'Madagascar': 'Madagascar',
  'Angola': 'Angola',
  'Mozambique': 'Mozambique',
  'Zimbabwe': 'Zimbabwe',
  'Argentina': 'Argentine',
  'Chile': 'Chili',
  'Peru': 'Pérou',
  'Colombia': 'Colombie',
  'Venezuela': 'Venezuela',
  'Cuba': 'Cuba',
  'Haiti': 'Haïti',
  'Taiwan': 'Taïwan',
  'Kosovo': 'Kosovo',
  'Palestine': 'Palestine',
  'W. Sahara': 'Sahara occidental',
  'Western Sahara': 'Sahara occidental',
};

// Mots-clés additionnels pour le filtre RSS par pays (extension du nom).
// Utilisés en plus du nom FR/EN pour augmenter le rappel sans changer la précision.
const COUNTRY_RSS_KEYWORDS = {
  'United States of America': ['états-unis', 'usa', 'américain', 'américaine', 'washington', 'trump', 'biden'],
  'Russia': ['russie', 'russe', 'moscou', 'poutine', 'kremlin'],
  'China': ['chine', 'chinois', 'chinoise', 'pékin', 'beijing', 'xi jinping'],
  'Ukraine': ['ukraine', 'ukrainien', 'kiev', 'kyiv', 'zelensky'],
  'Israel': ['israël', 'israélien', 'tel aviv', 'netanyahu', 'jérusalem'],
  'Palestine': ['palestine', 'palestinien', 'gaza', 'cisjordanie', 'hamas'],
  'France': ['france', 'français', 'française', 'paris', 'macron'],
  'United Kingdom': ['royaume-uni', 'britannique', 'londres', 'starmer'],
  'Germany': ['allemagne', 'allemand', 'allemande', 'berlin', 'scholz', 'merz'],
  'Iran': ['iran', 'iranien', 'iranienne', 'téhéran', 'khamenei'],
  'Syria': ['syrie', 'syrien', 'damas'],
  'Saudi Arabia': ['arabie saoudite', 'saoudien', 'riyad', 'mbs'],
  'Turkey': ['turquie', 'turc', 'ankara', 'erdogan'],
  'India': ['inde', 'indien', 'new delhi', 'modi'],
  'Pakistan': ['pakistan', 'pakistanais', 'islamabad'],
  'North Korea': ['corée du nord', 'nord-coréen', 'pyongyang', 'kim jong-un'],
  'South Korea': ['corée du sud', 'sud-coréen', 'séoul'],
  'Japan': ['japon', 'japonais', 'tokyo'],
  'Yemen': ['yémen', 'houthis'],
  'Lebanon': ['liban', 'libanais', 'beyrouth', 'hezbollah'],
  'Sudan': ['soudan', 'soudanais', 'khartoum'],
};

// ---------------------------------------------------------------------------
// 1. Chargement parallèle des données
// ---------------------------------------------------------------------------

async function loadJson(path) {
  const resp = await fetch(path);
  if (!resp.ok) throw new Error(`Échec chargement ${path}: ${resp.status}`);
  return resp.json();
}

async function loadAll() {
  const [world, sipri, rss] = await Promise.all([
    loadJson(DATA_PATHS.worldGeoJson),
    loadJson(DATA_PATHS.sipri),
    loadJson(DATA_PATHS.rss),
  ]);
  return { world, sipri, rss };
}

// ---------------------------------------------------------------------------
// 2. Jointure SIPRI ↔ Natural Earth (par nom de pays)
// ---------------------------------------------------------------------------

function buildSipriIndex(sipriData) {
  // Crée un index { nom_lowercase: { milex_usd, milex_pct_gdp } } pour
  // recherche rapide lors du parcours des features Natural Earth.
  const idx = {};
  const usdData = sipriData.indicators?.milex_constant_usd?.data || {};
  const pctData = sipriData.indicators?.milex_pct_gdp?.data || {};

  // Indexer les pays présents dans USD constants
  Object.keys(usdData).forEach((sipriName) => {
    const usdValue = usdData[sipriName]?.[TARGET_YEAR];
    const pctValue = pctData[sipriName]?.[TARGET_YEAR];
    const aliases = COUNTRY_NAME_ALIASES[sipriName] || [sipriName];
    aliases.forEach((alias) => {
      idx[alias.toLowerCase()] = {
        sipri_name: sipriName,
        milex_constant_usd: usdValue !== undefined ? usdValue : null,
        milex_pct_gdp: pctValue !== undefined ? pctValue : null,
      };
    });
  });
  return idx;
}

function joinSipriToFeatures(worldGeoJson, sipriIndex) {
  let matched = 0;
  let unmatched = [];
  worldGeoJson.features.forEach((feat) => {
    const props = feat.properties || {};
    const candidates = [props.name, props.name_long].filter(Boolean);
    let match = null;
    for (const candidate of candidates) {
      const found = sipriIndex[candidate.toLowerCase()];
      if (found) {
        match = found;
        break;
      }
    }
    if (match) {
      props.milex_constant_usd = match.milex_constant_usd;
      props.milex_pct_gdp = match.milex_pct_gdp;
      matched += 1;
    } else {
      props.milex_constant_usd = null;
      props.milex_pct_gdp = null;
      if (props.name) unmatched.push(props.name);
    }
  });
  return { matched, unmatched };
}

// ---------------------------------------------------------------------------
// 3. Initialisation MapLibre
// ---------------------------------------------------------------------------

function buildMap(worldGeoJson) {
  // Style minimaliste sans tuiles externes : on n'a besoin que des polygones
  // pays. Pas de fonds satellites ou Mapbox. 100% autonome.
  const map = new maplibregl.Map({
    container: 'map',
    style: {
      version: 8,
      sources: {
        countries: {
          type: 'geojson',
          data: worldGeoJson,
          generateId: true,
        },
      },
      layers: [
        // Fond clair
        {
          id: 'background',
          type: 'background',
          paint: { 'background-color': '#FAFAFA' },
        },
        // Remplissage choroplèthe (visibilité contrôlée par sélecteur)
        {
          id: 'countries-fill',
          type: 'fill',
          source: 'countries',
          paint: {
            'fill-color': '#FFFFFF',
            'fill-opacity': 0.9,
          },
        },
        // Bordures (toujours visibles)
        {
          id: 'countries-border',
          type: 'line',
          source: 'countries',
          paint: {
            'line-color': '#54595F',
            'line-width': 0.5,
          },
        },
        // Bordures des territoires disputés (mises en évidence)
        {
          id: 'countries-disputed',
          type: 'line',
          source: 'countries',
          filter: ['==', ['get', 'disputed'], true],
          paint: {
            'line-color': COUNTRY_BORDER_DISPUTED,
            'line-width': 1.6,
            'line-dasharray': [2, 2],
          },
        },
        // Couche de surbrillance au hover
        {
          id: 'countries-hover',
          type: 'fill',
          source: 'countries',
          paint: {
            'fill-color': '#62D0FF',
            'fill-opacity': [
              'case',
              ['boolean', ['feature-state', 'hover'], false],
              0.25,
              0,
            ],
          },
        },
      ],
    },
    center: [10, 25],
    zoom: 1.6,
    minZoom: 1,
    maxZoom: 6,
    attributionControl: false,
  });

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  map.addControl(
    new maplibregl.AttributionControl({
      compact: true,
      customAttribution: [
        '<a href="https://www.naturalearthdata.com/" target="_blank" rel="noopener">Natural Earth</a>',
        '<a href="https://www.sipri.org/databases/milex" target="_blank" rel="noopener">SIPRI</a>',
        '<a href="https://maplibre.org" target="_blank" rel="noopener">MapLibre</a>',
      ].join(' · '),
    }),
    'bottom-right',
  );

  return map;
}

// ---------------------------------------------------------------------------
// 4. Sélecteur d'indicateur — paint adaptatif
// ---------------------------------------------------------------------------

function buildFillExpression(indicator) {
  if (indicator === 'none') {
    return '#FFFFFF';
  }
  const stops = indicator === 'milex_constant_usd'
    ? CHOROPLETH_STOPS_USD
    : CHOROPLETH_STOPS_PCT_GDP;

  // Expression MapLibre : interpolation linéaire avec fallback gris si null
  return [
    'case',
    ['==', ['get', indicator], null],
    NO_DATA_COLOR,
    [
      'interpolate',
      ['linear'],
      ['to-number', ['get', indicator]],
      ...stops.flat(),
    ],
  ];
}

function applyIndicator(map, indicator) {
  map.setPaintProperty('countries-fill', 'fill-color', buildFillExpression(indicator));

  // Met à jour la légende
  const legend = document.getElementById('legend');
  const title = document.getElementById('legend-title');
  const scale = document.getElementById('legend-scale');
  const source = document.getElementById('legend-source');

  if (indicator === 'none') {
    legend.hidden = true;
    return;
  }
  legend.hidden = false;

  const stops = indicator === 'milex_constant_usd'
    ? CHOROPLETH_STOPS_USD
    : CHOROPLETH_STOPS_PCT_GDP;

  if (indicator === 'milex_constant_usd') {
    title.textContent = `Dépenses militaires ${TARGET_YEAR} — USD constants 2024`;
    source.textContent = 'Source : SIPRI MILEX · maj annuelle (avril)';
  } else {
    title.textContent = `Dépenses militaires ${TARGET_YEAR} — % du PIB`;
    source.textContent = 'Source : SIPRI MILEX · maj annuelle (avril)';
  }

  const min = stops[0][0];
  const max = stops[stops.length - 1][0];
  const formatMin = indicator === 'milex_constant_usd'
    ? `${(min / 1000).toFixed(0)} k$`
    : `${min} %`;
  const formatMax = indicator === 'milex_constant_usd'
    ? `${(max / 1000).toFixed(0)} k$`
    : `${max} %`;

  scale.innerHTML = `<span>${formatMin}</span><div class="legend-scale-bar"></div><span>${formatMax}</span>`;
}

// ---------------------------------------------------------------------------
// 5. Tooltip au clic sur un pays
// ---------------------------------------------------------------------------

const tooltip = document.getElementById('tooltip');
let currentIndicator = 'none';

function formatValue(indicator, value) {
  if (value === null || value === undefined) return null;
  if (indicator === 'milex_constant_usd') {
    const usd = Number(value).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
    const eur = (Number(value) * EUR_PER_USD_2024).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
    return `${usd} M USD <span class="value-secondary">(≈ ${eur} M EUR)</span>`;
  }
  if (indicator === 'milex_pct_gdp') {
    return `${Number(value).toFixed(2)} %`;
  }
  return String(value);
}

function frenchName(enName) {
  if (!enName) return null;
  return COUNTRY_NAME_FR[enName] || enName;
}

function frenchContinent(continent) {
  if (!continent) return '';
  return CONTINENT_FR[continent] || continent;
}

function frenchSubregion(subregion) {
  if (!subregion) return '';
  return SUBREGION_FR[subregion] || subregion;
}

function showTooltip(event, feature) {
  const props = feature.properties || {};
  // Préférer name_fr du GeoJSON, sinon traduire via COUNTRY_NAME_FR, sinon nom anglais
  const name = props.name_fr || frenchName(props.name) || props.name || '(sans nom)';
  const isDisputed = props.disputed === true || props.disputed === 'true';

  let valueHtml = '';
  if (currentIndicator !== 'none') {
    const v = props[currentIndicator];
    const formatted = formatValue(currentIndicator, v);
    if (formatted !== null) {
      const unit = currentIndicator === 'milex_constant_usd'
        ? `USD constants 2024 · année ${TARGET_YEAR}`
        : `% du PIB · année ${TARGET_YEAR}`;
      valueHtml = `
        <div class="tooltip-value">${formatted}</div>
        <div class="tooltip-unit">${unit}</div>
      `;
    } else {
      valueHtml = `<div class="tooltip-unit">Donnée non disponible pour ${TARGET_YEAR}.</div>`;
    }
  } else {
    valueHtml = `<div class="tooltip-unit">Sélectionnez un indicateur en haut à gauche pour afficher les données.</div>`;
  }

  let disputedHtml = '';
  if (isDisputed && props.dispute_note) {
    disputedHtml = `<div class="tooltip-disputed"><strong>Statut disputé.</strong> ${props.dispute_note}</div>`;
  }

  const sourceHtml = currentIndicator === 'none'
    ? ''
    : `<div class="tooltip-source">${currentIndicator === 'milex_constant_usd'
        ? 'Source SIPRI MILEX (★★★★)'
        : 'Source SIPRI MILEX (★★★★) — ratio dépenses militaires / PIB'}</div>`;

  const continentFr = frenchContinent(props.continent);
  const subregionFr = frenchSubregion(props.subregion);
  const metaParts = [continentFr, subregionFr].filter(Boolean);

  tooltip.innerHTML = `
    <h4>${escapeHtml(name)}</h4>
    <div class="tooltip-meta">${escapeHtml(metaParts.join(' · '))}</div>
    ${valueHtml}
    ${disputedHtml}
    ${sourceHtml}
  `;

  tooltip.dataset.disputed = isDisputed ? 'true' : 'false';

  // Positionnement près du curseur, en évitant de sortir de l'écran
  const x = event.point.x;
  const y = event.point.y;
  const mapEl = document.getElementById('map');
  const mapRect = mapEl.getBoundingClientRect();
  const ttWidth = 280;
  const ttHeight = 200;

  let left = x + 16;
  let top = y + 16;
  if (left + ttWidth > mapRect.width) left = x - ttWidth - 16;
  if (top + ttHeight > mapRect.height) top = y - ttHeight - 16;
  if (left < 0) left = 8;
  if (top < 0) top = 8;

  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
  tooltip.hidden = false;
}

function hideTooltip() {
  tooltip.hidden = true;
}

// ---------------------------------------------------------------------------
// 6. Sidebar RSS
// ---------------------------------------------------------------------------

function formatDate(isoString) {
  if (!isoString) return '';
  try {
    const d = new Date(isoString);
    return d.toLocaleString('fr-FR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (_) {
    return '';
  }
}

// État global du filtre RSS par pays (null = tous les items affichés)
let rssAllItems = [];
let rssCurrentFilter = null;
let rssSourceName = 'France 24';
let rssFetchedAt = null;

function renderRss(rssData) {
  rssAllItems = rssData.items || [];
  rssSourceName = rssData.source?.name || 'France 24';
  rssFetchedAt = formatDate(rssData.fetched_at_utc);
  applyRssFilter(null);
}

function buildCountryKeywords(countryNameEn) {
  // Construit la liste de mots-clés pour filtrer le RSS sur un pays donné.
  // Sources : nom EN, nom FR, alias COUNTRY_RSS_KEYWORDS si présents.
  if (!countryNameEn) return [];
  const keywords = new Set();
  keywords.add(countryNameEn.toLowerCase());
  const fr = COUNTRY_NAME_FR[countryNameEn];
  if (fr) keywords.add(fr.toLowerCase());
  const extras = COUNTRY_RSS_KEYWORDS[countryNameEn] || [];
  extras.forEach((k) => keywords.add(k.toLowerCase()));
  return Array.from(keywords);
}

function itemMatchesKeywords(item, keywords) {
  if (keywords.length === 0) return true;
  const haystack = `${item.title || ''} ${item.summary || ''}`.toLowerCase();
  return keywords.some((k) => haystack.includes(k));
}

function applyRssFilter(countryNameEn) {
  // countryNameEn === null → tous les items
  // sinon → items contenant un mot-clé pays
  rssCurrentFilter = countryNameEn;
  const keywords = buildCountryKeywords(countryNameEn);
  const filtered = countryNameEn
    ? rssAllItems.filter((item) => itemMatchesKeywords(item, keywords))
    : rssAllItems;

  const list = document.getElementById('rss-list');
  const meta = document.getElementById('rss-meta');

  if (countryNameEn) {
    const fr = COUNTRY_NAME_FR[countryNameEn] || countryNameEn;
    meta.innerHTML = `Filtre : <strong>${escapeHtml(fr)}</strong> · ${filtered.length} dépêche${filtered.length > 1 ? 's' : ''} · <a href="#" id="rss-clear-filter">tout afficher</a>`;
    document.getElementById('rss-clear-filter')?.addEventListener('click', (e) => {
      e.preventDefault();
      applyRssFilter(null);
    });
  } else {
    meta.textContent = `${rssSourceName} · ${rssAllItems.length} dépêches · maj ${rssFetchedAt}`;
  }

  list.innerHTML = '';
  if (filtered.length === 0) {
    const li = document.createElement('li');
    li.className = 'rss-item';
    li.innerHTML = `<p class="rss-summary"><em>Aucune dépêche directement liée à ce pays dans le flux courant.</em></p>`;
    list.appendChild(li);
    return;
  }
  filtered.slice(0, 25).forEach((item) => {
    const li = document.createElement('li');
    li.className = 'rss-item';
    li.innerHTML = `
      <a href="${item.link}" target="_blank" rel="noopener">${escapeHtml(item.title || '(sans titre)')}</a>
      ${item.summary ? `<p class="rss-summary">${escapeHtml(item.summary)}</p>` : ''}
      <div class="rss-date">${formatDate(item.published_utc) || item.published_raw || ''}</div>
    `;
    list.appendChild(li);
  });
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ---------------------------------------------------------------------------
// 7. Étiquettes pays sur la carte (centroïdes + markers HTML)
// ---------------------------------------------------------------------------

function computeCentroid(geometry) {
  // Centroïde approximatif (moyenne des sommets du plus grand polygone) pour
  // positionner une étiquette. Suffisant pour des polygones nationaux.
  if (!geometry) return null;
  let ring = null;
  if (geometry.type === 'Polygon') {
    ring = geometry.coordinates[0];
  } else if (geometry.type === 'MultiPolygon') {
    let maxLen = 0;
    geometry.coordinates.forEach((poly) => {
      if (poly[0].length > maxLen) {
        maxLen = poly[0].length;
        ring = poly[0];
      }
    });
  }
  if (!ring || ring.length === 0) return null;
  let sumLng = 0;
  let sumLat = 0;
  ring.forEach(([lng, lat]) => {
    sumLng += lng;
    sumLat += lat;
  });
  return [sumLng / ring.length, sumLat / ring.length];
}

// Liste des markers de labels, conservée pour ajuster visibilité et taille
// au changement de zoom (cf. updateLabelVisibility / map.on('zoom', ...)).
let labelMarkers = [];

function shouldShowLabel(labelrank, zoom) {
  // Filtre progressif par importance Natural Earth :
  //   zoom < 2  → seulement les pays majeurs (LABELRANK ≤ 2 : ~20 entités)
  //   zoom 2-3  → LABELRANK ≤ 4 (~50)
  //   zoom 3-4  → LABELRANK ≤ 6 (~100)
  //   zoom ≥ 4  → tous les pays
  // Pour les features sans labelrank renseigné (rare), on tolère à partir
  // d'un zoom moyen pour ne pas perdre les territoires marginaux.
  if (labelrank === null || labelrank === undefined) return zoom >= 3;
  if (zoom < 2) return labelrank <= 2;
  if (zoom < 3) return labelrank <= 4;
  if (zoom < 4) return labelrank <= 6;
  return true;
}

function getLabelFontSize(zoom) {
  // Échelle linéaire bornée : 9 px à zoom 1, 14 px à zoom 5+
  return Math.round(Math.max(9, Math.min(14, 7.5 + zoom * 1.3)));
}

function updateLabelVisibility(zoom) {
  const fontSize = getLabelFontSize(zoom);
  document.documentElement.style.setProperty('--label-size', `${fontSize}px`);
  labelMarkers.forEach(({ marker, labelrank }) => {
    const el = marker.getElement();
    el.style.display = shouldShowLabel(labelrank, zoom) ? '' : 'none';
  });
}

function addCountryLabels(map, geojson) {
  // Crée un marker MapLibre par pays (élément HTML). Pour ~177 pays Natural
  // Earth 110m, l'impact perf reste acceptable. Si on monte à 1:10m (~5000
  // features), basculer sur une couche symbol + glyphs CDN.
  labelMarkers = [];
  geojson.features.forEach((feat) => {
    const props = feat.properties || {};
    const label = props.name_fr || COUNTRY_NAME_FR[props.name] || props.name;
    if (!label) return;
    const centroid = computeCentroid(feat.geometry);
    if (!centroid) return;

    const el = document.createElement('div');
    el.className = 'country-label';
    if (props.disputed === true || props.disputed === 'true') {
      el.classList.add('disputed');
    }
    el.textContent = label;

    const marker = new maplibregl.Marker({ element: el, anchor: 'center' })
      .setLngLat(centroid)
      .addTo(map);

    labelMarkers.push({
      marker,
      labelrank: typeof props.labelrank === 'number' ? props.labelrank : null,
    });
  });

  // Synchronise visibilité et taille avec le zoom courant
  updateLabelVisibility(map.getZoom());
  map.on('zoom', () => updateLabelVisibility(map.getZoom()));
}

// ---------------------------------------------------------------------------
// 8. Bootstrap principal
// ---------------------------------------------------------------------------

(async function bootstrap() {
  const loadingEl = document.getElementById('loading');
  try {
    const { world, sipri, rss } = await loadAll();
    console.log(
      `[SAT-GEO] Sources chargées : ${world.features?.length} pays Natural Earth, `
      + `${Object.keys(sipri.indicators?.milex_constant_usd?.data || {}).length} pays SIPRI USD, `
      + `${rss.items?.length} dépêches RSS`,
    );

    // Jointure SIPRI ↔ Natural Earth
    const sipriIndex = buildSipriIndex(sipri);
    const { matched, unmatched } = joinSipriToFeatures(world, sipriIndex);
    console.log(
      `[SAT-GEO] Jointure SIPRI : ${matched} pays matchés. `
      + `${unmatched.length} pays Natural Earth sans donnée SIPRI ${TARGET_YEAR}.`,
    );
    if (unmatched.length > 0) {
      console.log('[SAT-GEO] Pays non matchés (à investiguer si stratégiques) :', unmatched);
    }

    const map = buildMap(world);

    // RSS
    renderRss(rss);

    // Sélecteur d'indicateur
    const buttons = document.querySelectorAll('.indicator-btn');
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        buttons.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        currentIndicator = btn.dataset.indicator;
        applyIndicator(map, currentIndicator);
        hideTooltip();
      });
    });

    map.on('load', () => {
      loadingEl.classList.add('hidden');

      // Interactions souris : hover et clic
      let hoveredId = null;
      map.on('mousemove', 'countries-fill', (e) => {
        if (!e.features || e.features.length === 0) return;
        map.getCanvas().style.cursor = 'pointer';
        if (hoveredId !== null) {
          map.setFeatureState({ source: 'countries', id: hoveredId }, { hover: false });
        }
        hoveredId = e.features[0].id;
        map.setFeatureState({ source: 'countries', id: hoveredId }, { hover: true });
      });

      map.on('mouseleave', 'countries-fill', () => {
        map.getCanvas().style.cursor = '';
        if (hoveredId !== null) {
          map.setFeatureState({ source: 'countries', id: hoveredId }, { hover: false });
        }
        hoveredId = null;
      });

      map.on('click', 'countries-fill', (e) => {
        if (!e.features || e.features.length === 0) {
          hideTooltip();
          return;
        }
        const feat = e.features[0];
        showTooltip(e, feat);
        // Filtre RSS par pays cliqué
        const countryNameEn = feat.properties?.name;
        if (countryNameEn) {
          applyRssFilter(countryNameEn);
        }
      });

      // Clic en dehors d'un pays ferme le tooltip et le filtre
      map.on('click', (e) => {
        const features = map.queryRenderedFeatures(e.point, { layers: ['countries-fill'] });
        if (features.length === 0) {
          hideTooltip();
          applyRssFilter(null);
        }
      });

      // Ajout des étiquettes des pays après le chargement de la carte
      addCountryLabels(map, world);
    });

  } catch (err) {
    console.error('[SAT-GEO] Erreur d\'initialisation :', err);
    loadingEl.innerHTML = `
      <div style="text-align: center;">
        <p><strong>Impossible de charger le tableau de bord.</strong></p>
        <p style="font-size: 13px; opacity: 0.8;">${escapeHtml(err.message || String(err))}</p>
        <p style="font-size: 11px; margin-top: 16px; opacity: 0.6;">Vérifier que les scripts d'ingestion ont bien été exécutés et que le serveur sert le dossier <code>site/</code>.</p>
      </div>
    `;
  }
})();
