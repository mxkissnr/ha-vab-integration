/**
 * vab-departures-card
 * Custom Lovelace card for real-time VAB bus/train departures.
 * https://github.com/mxkissnr/vab-departures-card
 */

function esc(str) {
  return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

const THEMES = {
  'swiss-db': {
    label: 'Swiss/DB Signage',
    fontImport: "@import url('https://fonts.googleapis.com/css2?family=Fira+Sans+Condensed:wght@500;700;800&display=swap');",
    multiLine: true,
    lineColors: ['#1a3a5c', '#8b1e3f', '#0f5c4a', '#a34d0e', '#4a4a8f', '#6b5a1f', '#2d5a6b', '#7a2d2d'],
    vars: {
      '--vab-font': "'Fira Sans Condensed','Arial Narrow',sans-serif",
      '--vab-dot-live': '#1a3a5c',
      '--vab-mins-now': '#c0272d',
      '--vab-delay': '#b8860b',
      '--vab-delay-severe': '#c0272d',
      '--vab-ontime': '#3f6b4f',
      '--vab-warn': '#b8860b',
      '--vab-nextday': '#c0272d',
    },
  },
  'led': {
    label: 'LED-Fahrtzielanzeige',
    fontImport: "@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');",
    multiLine: false,
    lineColors: ['#ff8c1a'],
    vars: {
      '--vab-font': "'Share Tech Mono',ui-monospace,monospace",
      '--vab-bg': '#0d0d0d',
      '--vab-header-color': '#ff8c1a',
      '--vab-header-transform': 'uppercase',
      '--vab-header-tracking': '.12em',
      '--vab-header-weight': '400',
      '--vab-text': '#ff8c1a',
      '--vab-text-dim': 'rgba(255,140,26,.5)',
      '--vab-divider-color': 'rgba(255,140,26,.18)',
      '--vab-row-hover-bg': 'rgba(255,140,26,.06)',
      '--vab-dot-radius': '0',
      '--vab-dot-live': '#ff8c1a',
      '--vab-dot-planned': 'rgba(255,140,26,.3)',
      '--vab-glow': '0 0 4px rgba(255,140,26,.7)',
      '--vab-text-glow': '0 0 6px rgba(255,140,26,.4)',
      '--vab-badge-radius': '0',
      '--vab-badge-border': '1px solid var(--line-color)',
      '--vab-badge-bg': 'transparent',
      '--vab-badge-color': 'var(--line-color)',
      '--vab-badge-weight': '400',
      '--vab-direction-weight': '400',
      '--vab-mins-now': '#ff8c1a',
      '--vab-mins-weight': '400',
      '--vab-delay': '#ff8c1a',
      '--vab-delay-severe': '#ff8c1a',
      '--vab-ontime': 'rgba(255,140,26,.5)',
      '--vab-warn': '#ff8c1a',
      '--vab-nextday': '#ff8c1a',
      '--vab-blink': 'vabBlink 1.2s steps(2) infinite',
    },
  },
  'flap': {
    label: 'Split-Flap / Solari Board',
    fontImport: "@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');",
    multiLine: false,
    lineColors: ['#f5a623'],
    vars: {
      '--vab-font': "'Space Mono',ui-monospace,monospace",
      '--vab-bg': '#161616',
      '--vab-header-color': '#f5a623',
      '--vab-header-transform': 'uppercase',
      '--vab-header-tracking': '.1em',
      '--vab-header-weight': '700',
      '--vab-text': '#f5a623',
      '--vab-text-dim': 'rgba(245,166,35,.55)',
      '--vab-divider-color': 'rgba(255,255,255,.15)',
      '--vab-row-hover-bg': 'rgba(245,166,35,.08)',
      '--vab-dot-radius': '0',
      '--vab-dot-live': '#f5a623',
      '--vab-dot-planned': 'rgba(245,166,35,.3)',
      '--vab-badge-radius': '0',
      '--vab-badge-border': '1.5px solid var(--line-color)',
      '--vab-badge-bg': 'transparent',
      '--vab-badge-color': 'var(--line-color)',
      '--vab-badge-weight': '700',
      '--vab-mins-now': '#f5a623',
      '--vab-mins-weight': '700',
      '--vab-delay': '#f5a623',
      '--vab-delay-severe': '#f5a623',
      '--vab-ontime': 'rgba(245,166,35,.55)',
      '--vab-warn': '#f5a623',
      '--vab-nextday': '#f5a623',
    },
  },
  'vignelli': {
    label: 'Vignelli Subway Circles',
    fontImport: "@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;900&display=swap');",
    multiLine: true,
    lineColors: ['#0039a6', '#00933c', '#ee352e', '#ff6319', '#b933ad', '#00add0', '#996633', '#808183'],
    vars: {
      '--vab-font': "'Archivo',sans-serif",
      '--vab-bg': '#ffffff',
      '--vab-header-color': '#111111',
      '--vab-header-transform': 'uppercase',
      '--vab-header-tracking': '.08em',
      '--vab-header-weight': '900',
      '--vab-text': '#111111',
      '--vab-text-dim': '#555555',
      '--vab-divider-color': '#111111',
      '--vab-row-hover-bg': '#f2f2f2',
      '--vab-dot-radius': '0',
      '--vab-dot-live': '#111111',
      '--vab-dot-planned': '#bbbbbb',
      '--vab-badge-radius': '50%',
      '--vab-badge-border': 'none',
      '--vab-badge-bg': 'var(--line-color)',
      '--vab-badge-color': '#ffffff',
      '--vab-badge-weight': '900',
      '--vab-direction-weight': '600',
      '--vab-mins-now': '#ee352e',
      '--vab-mins-weight': '900',
      '--vab-delay': '#ee352e',
      '--vab-delay-severe': '#ee352e',
      '--vab-ontime': '#111111',
      '--vab-warn': '#ee352e',
      '--vab-nextday': '#ee352e',
    },
  },
  'receipt': {
    label: 'Thermal Ticket Receipt',
    fontImport: "@import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');",
    multiLine: false,
    lineColors: ['#2a2a26'],
    vars: {
      '--vab-font': "'Courier Prime',monospace",
      '--vab-bg': '#f2f0ea',
      '--vab-header-color': '#2a2a26',
      '--vab-header-transform': 'uppercase',
      '--vab-header-tracking': '.1em',
      '--vab-header-weight': '700',
      '--vab-text': '#2a2a26',
      '--vab-text-dim': '#8a8578',
      '--vab-divider-color': '#b9b6ac',
      '--vab-divider-style': 'dashed',
      '--vab-row-hover-bg': '#e9e6dc',
      '--vab-dot-radius': '0',
      '--vab-dot-live': '#2a2a26',
      '--vab-dot-planned': '#c3c0b4',
      '--vab-badge-radius': '0',
      '--vab-badge-border': 'none',
      '--vab-badge-bg': 'transparent',
      '--vab-badge-color': 'var(--line-color)',
      '--vab-badge-weight': '700',
      '--vab-mins-now': '#b3261e',
      '--vab-mins-weight': '700',
      '--vab-delay': '#b3261e',
      '--vab-delay-severe': '#b3261e',
      '--vab-ontime': '#5a7c5f',
      '--vab-warn': '#b3261e',
      '--vab-nextday': '#b3261e',
    },
  },
  'shelter': {
    label: 'Night Bus Shelter Glow',
    fontImport: "@import url('https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;500;600&display=swap');",
    multiLine: false,
    lineColors: ['#ffb454'],
    vars: {
      '--vab-font': "'Libre Franklin',sans-serif",
      '--vab-bg': '#131a2e',
      '--vab-header-color': '#ffb454',
      '--vab-header-weight': '600',
      '--vab-text': '#eee7d8',
      '--vab-text-dim': 'rgba(238,231,216,.55)',
      '--vab-divider-color': 'rgba(255,180,84,.14)',
      '--vab-row-hover-bg': 'rgba(255,180,84,.06)',
      '--vab-dot-live': '#ffb454',
      '--vab-dot-planned': 'rgba(255,180,84,.3)',
      '--vab-glow': '0 0 6px 1px rgba(255,180,84,.7)',
      '--vab-text-glow': '0 0 8px rgba(255,180,84,.5)',
      '--vab-badge-radius': '0',
      '--vab-badge-border': 'none',
      '--vab-badge-bg': 'transparent',
      '--vab-badge-color': 'var(--line-color)',
      '--vab-mins-now': '#ffb454',
      '--vab-mins-weight': '600',
      '--vab-delay': '#ff6b4a',
      '--vab-delay-severe': '#ff6b4a',
      '--vab-ontime': 'rgba(238,231,216,.6)',
      '--vab-warn': '#ffb454',
      '--vab-nextday': '#ff6b4a',
    },
  },
  'topo': {
    label: 'Alpine Topo Ledger',
    fontImport: "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Libre+Franklin:wght@400;500;600&display=swap');",
    multiLine: false,
    lineColors: ['#4a6741'],
    vars: {
      '--vab-font': "'Libre Franklin',sans-serif",
      '--vab-header-font': "'Fraunces',serif",
      '--vab-bg': '#efece2',
      '--vab-header-color': '#26362b',
      '--vab-header-weight': '600',
      '--vab-text': '#232620',
      '--vab-text-dim': '#77705f',
      '--vab-divider-color': 'rgba(90,60,30,.3)',
      '--vab-divider-style': 'dashed',
      '--vab-row-hover-bg': '#e5e1d3',
      '--vab-dot-radius': '0',
      '--vab-dot-live': '#4a6741',
      '--vab-dot-planned': '#b7b2a1',
      '--vab-badge-radius': '0',
      '--vab-badge-border': '1.5px solid var(--line-color)',
      '--vab-badge-bg': 'transparent',
      '--vab-badge-color': 'var(--line-color)',
      '--vab-mins-now': '#a3552e',
      '--vab-delay': '#a3552e',
      '--vab-delay-severe': '#a3552e',
      '--vab-ontime': '#4a6741',
      '--vab-warn': '#a3552e',
      '--vab-nextday': '#a3552e',
    },
  },
  'ledger': {
    label: 'Fahrplanbuch-Ledger',
    fontImport: "@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');",
    multiLine: false,
    lineColors: ['#2b3a67'],
    vars: {
      '--vab-font': "'IBM Plex Mono',monospace",
      '--vab-bg': '#f7f4ec',
      '--vab-header-color': '#2b3a67',
      '--vab-header-transform': 'uppercase',
      '--vab-header-tracking': '.06em',
      '--vab-header-weight': '600',
      '--vab-text': '#1a1a1a',
      '--vab-text-dim': '#77705f',
      '--vab-divider-color': 'rgba(26,26,26,.15)',
      '--vab-row-hover-bg': '#eeebe1',
      '--vab-dot-radius': '0',
      '--vab-dot-live': '#2b3a67',
      '--vab-dot-planned': '#b0ab9c',
      '--vab-badge-radius': '0',
      '--vab-badge-border': 'none',
      '--vab-badge-bg': 'transparent',
      '--vab-badge-color': 'var(--line-color)',
      '--vab-badge-weight': '600',
      '--vab-mins-now': '#b3261e',
      '--vab-delay': '#b3261e',
      '--vab-delay-severe': '#b3261e',
      '--vab-ontime': '#3f6b4f',
      '--vab-warn': '#2b3a67',
      '--vab-nextday': '#b3261e',
    },
  },
};

function themeKey(config) {
  return THEMES[config?.theme] ? config.theme : 'swiss-db';
}

function themeVarsCss(key) {
  const t = THEMES[key] || THEMES['swiss-db'];
  const decls = Object.entries(t.vars).map(([k, v]) => `${k}: ${v};`).join(' ');
  return `${t.fontImport}\n  ha-card.theme-${key} { ${decls} }`;
}

function lineColor(line, config) {
  const theme = THEMES[themeKey(config)];
  const custom = config?.line_colors?.[String(line)];
  // Only accept hex colors — anything else could inject CSS via the style attribute
  if (custom && /^#[0-9a-f]{3,8}$/i.test(custom)) return custom;
  if (!theme.multiLine) return theme.lineColors[0];
  let hash = 0;
  for (const c of String(line)) hash = (hash * 31 + c.charCodeAt(0)) & 0xff;
  return theme.lineColors[hash % theme.lineColors.length];
}

function fmtMinutes(mins) {
  if (mins <= 0) return 'jetzt';
  if (mins < 60) return `${mins} min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m === 0 ? `${h}h` : `${h}h ${m}min`;
}

function fmtTime(isoString) {
  if (!isoString) return '';
  try {
    return new Date(isoString).toLocaleTimeString('de-DE', {
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return ''; }
}

// ─────────────────────────────────────────────
//  Card
// ─────────────────────────────────────────────

class VabDeparturesCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    try {
      this._expanded = new Set(JSON.parse(localStorage.getItem('vab-expanded') || '[]'));
    } catch {
      this._expanded = new Set();
    }
  }

  set hass(hass) {
    this._hass = hass;
    const entityIds = this._resolveEntities();
    const key = entityIds.map(id => {
      const s = hass.states[id];
      return s ? JSON.stringify(s.attributes.departures) + '|' + JSON.stringify(s.attributes.watched) : 'x';
    }).join('|');
    if (key !== this._renderKey) {
      this._renderKey = key;
      this._render();
    }
  }

  setConfig(config) {
    const c = config ?? {};
    // Backwards-compat: if entities already set and auto_entities not explicitly given → manual
    this._config = { auto_entities: !c.entities?.length, ...c };
  }

  static getConfigElement() {
    return document.createElement('vab-departures-card-editor');
  }

  static getStubConfig() {
    return { title: '', auto_entities: true };
  }

  _getVabEntities() {
    if (!this._hass) return [];
    return Object.keys(this._hass.states).filter(
      id => 'departures' in (this._hass.states[id].attributes || {})
    );
  }

  _resolveEntities() {
    return this._config.auto_entities !== false
      ? this._getVabEntities()
      : (this._config.entities || []);
  }

  _render() {
    if (!this._hass || !this._config) return;

    const entityIds = this._resolveEntities();

    const stops = entityIds.map(id => this._hass.states[id]).filter(Boolean);

    const theme = themeKey(this._config);

    this.shadowRoot.innerHTML = `
      <style>${themeVarsCss(theme)}${CARD_STYLES}</style>
      <ha-card class="theme-${theme}">
        ${this._config.title ? `<h1 class="card-header">${esc(this._config.title)}</h1>` : ''}
        ${stops.map(s => this._renderStop(s)).join('<div class="stop-divider"></div>')}
        ${!stops.length ? '<div class="empty">Keine Entitäten gefunden.</div>' : ''}
      </ha-card>
    `;

    this.shadowRoot.querySelectorAll('.stop-header.collapsible').forEach(el => {
      el.addEventListener('click', () => {
        const key = el.dataset.key;
        this._expanded.has(key) ? this._expanded.delete(key) : this._expanded.add(key);
        try { localStorage.setItem('vab-expanded', JSON.stringify([...this._expanded])); } catch {}
        this._renderKey = null;
        this._render();
      });
    });

    this.shadowRoot.querySelectorAll('.row-star').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const row = btn.closest('.row');
        const dep = { line: row.dataset.starLine, direction: row.dataset.starDir, planned: row.dataset.starPlanned };
        this._toggleStar(row.dataset.starEntity, dep);
      });
    });
  }

  _renderStop(state) {
    const attrs = state.attributes;
    const departures = attrs.departures || [];
    const watched = new Set(attrs.watched || []);
    const dirFilter = (attrs.direction_filter || []).map(esc).join(' / ');
    const stopLabel = dirFilter
      ? `${esc(attrs.stop_name)} <span class="dir-label">→ ${dirFilter}</span>`
      : esc(attrs.stop_name);

    const collapseKey = state.entity_id;
    const isCollapsed = !this._expanded.has(collapseKey);
    const visible = isCollapsed ? departures.slice(0, 1) : departures;

    const rows = visible.length
      ? visible.map(d => this._renderRow(d, state.entity_id, watched)).join('')
      : '<div class="no-dep">Keine Abfahrten</div>';

    const chevron = departures.length > 1
      ? `<span class="chevron">${isCollapsed ? '▶' : '▼'}</span>`
      : '';

    return `
      <div class="stop-section">
        <div class="stop-header ${departures.length > 1 ? 'collapsible' : ''}"
             data-key="${esc(collapseKey)}">
          ${chevron}${stopLabel}
        </div>
        ${rows}
        ${isCollapsed && departures.length > 1
          ? `<div class="collapsed-hint">+${departures.length - 1} weitere</div>`
          : ''}
      </div>
    `;
  }

  _starKey(dep) {
    return `${dep.line}|${dep.direction}|${dep.planned}`;
  }

  _toggleStar(entityId, dep) {
    if (!this._hass || !entityId) return;
    const watched = new Set(this._hass.states[entityId]?.attributes?.watched || []);
    const service = watched.has(this._starKey(dep)) ? 'unwatch_departure' : 'watch_departure';
    const data = { entity_id: entityId, line: dep.line, direction: dep.direction, planned: dep.planned };
    if (service === 'watch_departure') {
      data.leave_threshold = this._config.leave_threshold ?? 2;
      if (this._config.notify_service) data.notify_service = this._config.notify_service;
    }
    this._hass.callService('vab', service, data);
  }

  _renderRow(dep, entityId, watched) {
    const color     = lineColor(dep.line, this._config);
    const mins      = dep.minutes_until ?? 0;
    const delay     = dep.delay_minutes ?? 0;
    const isNow     = mins <= 0;
    const clockTime = fmtTime(dep.effective);

    const threshold = this._config.leave_threshold ?? 2;
    const leaveMins = dep.leave_in_minutes;
    const leaveDue  = leaveMins != null && leaveMins <= threshold;

    const isNextDay = dep.effective
      && new Date(dep.effective).toDateString() !== new Date().toDateString();

    const starred = watched.has(this._starKey(dep));

    const delayHtml = delay > 0
      ? `<span class="delay ${delay >= 5 ? 'severe' : ''}">&nbsp;+${delay} min</span>`
      : (dep.monitored ? `<span class="on-time">✓</span>` : '');

    const platformHtml = dep.platform
      ? `<span class="platform">Stg.&nbsp;${esc(dep.platform)}</span>`
      : '';

    return `
      <div class="row ${isNow ? 'now-row' : ''} ${leaveDue ? 'leave-now' : ''} ${starred ? 'starred-row' : ''}"
           data-star-entity="${esc(entityId)}" data-star-line="${esc(dep.line)}" data-star-dir="${esc(dep.direction)}" data-star-planned="${esc(dep.planned)}">
        <div class="dot ${dep.monitored ? 'live' : 'planned'}"
             title="${dep.monitored ? 'Live' : 'Fahrplan'}"></div>
        <div class="badge" style="--line-color:${esc(color)}">${esc(dep.line)}</div>
        <div class="middle">
          <span class="direction">${esc(dep.direction)}</span>
          ${platformHtml}
        </div>
        <div class="time-col">
          <span class="mins ${isNow ? 'now' : ''}">${fmtMinutes(mins)}</span>
          ${clockTime ? `<span class="clock-time">${clockTime}</span>` : ''}
          ${delayHtml}
          ${isNextDay ? `<span class="next-day-badge">Morgen früh</span>` : ''}
          ${leaveDue ? `<span class="leave-badge">Jetzt los!</span>` : (leaveMins != null && leaveMins > threshold && leaveMins <= 60 ? `<span class="leave-soon">Los in ${leaveMins} min</span>` : '')}
        </div>
        <button class="row-star${starred ? ' starred' : ''}" title="${starred ? 'Beobachtung entfernen' : 'Benachrichtigung wenn los'}">★</button>
      </div>
    `;
  }

}

// ─────────────────────────────────────────────
//  Editor
// ─────────────────────────────────────────────

class VabDeparturesCardEditor extends HTMLElement {
  setConfig(config) {
    const c = config ?? {};
    this._config = { entities: [], title: '', auto_entities: !c.entities?.length, ...c };
    this._build();
  }

  set hass(hass) {
    this._hass = hass;
    const vabEntities = this._getVabEntities();
    this.querySelectorAll('ha-entity-picker').forEach(p => {
      p.hass = hass;
      p.includeEntities = vabEntities;
    });
  }

  _getVabEntities() {
    if (!this._hass) return [];
    return Object.keys(this._hass.states).filter(
      id => 'departures' in (this._hass.states[id].attributes || {})
    );
  }

  _build() {
    if (!this._config) return;
    this.innerHTML = `<style>${EDITOR_STYLES}</style><div class="cfg"></div>`;
    const cfg = this.querySelector('.cfg');

    // Title
    const titleField = document.createElement('ha-textfield');
    titleField.label = 'Titel (optional)';
    titleField.value = this._config.title || '';
    titleField.style.cssText = 'width:100%;display:block;margin-bottom:12px';
    titleField.addEventListener('change', e => {
      this._fire({ ...this._config, title: e.target.value || undefined });
    });
    cfg.appendChild(titleField);

    // Theme picker
    const themeLbl = document.createElement('div');
    themeLbl.className = 'section-label';
    themeLbl.textContent = 'Design';
    cfg.appendChild(themeLbl);

    const themeSel = document.createElement('select');
    themeSel.className = 'notify-select';
    themeSel.style.cssText = 'width:100%;display:block;margin-bottom:12px';
    Object.entries(THEMES).forEach(([key, t]) => {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = t.label;
      if (key === themeKey(this._config)) opt.selected = true;
      themeSel.appendChild(opt);
    });
    themeSel.addEventListener('change', e => {
      this._fire({ ...this._config, theme: e.target.value });
    });
    cfg.appendChild(themeSel);

    // Walk-time threshold
    const thresholdField = document.createElement('ha-textfield');
    thresholdField.label = 'Gehzeit-Schwelle (Minuten, Standard 2)';
    thresholdField.type = 'number';
    thresholdField.value = this._config.leave_threshold ?? 2;
    thresholdField.style.cssText = 'width:100%;display:block;margin-bottom:12px';
    thresholdField.addEventListener('change', e => {
      const val = parseInt(e.target.value);
      this._fire({ ...this._config, leave_threshold: isNaN(val) ? undefined : val });
    });
    cfg.appendChild(thresholdField);

    // Notify service picker
    const mobileServices = Object.keys(this._hass?.services?.notify || {})
      .filter(s => s.startsWith('mobile_app_'));
    if (mobileServices.length) {
      const notifyLbl = document.createElement('div');
      notifyLbl.className = 'section-label';
      notifyLbl.textContent = 'Benachrichtigungs-Gerät';
      cfg.appendChild(notifyLbl);

      const notifyHint = document.createElement('div');
      notifyHint.className = 'notify-hint';
      notifyHint.textContent = 'Push-Notification wenn Stern-Abfahrt bevorsteht (HA Companion App)';
      cfg.appendChild(notifyHint);

      const notifyRow = document.createElement('div');
      notifyRow.className = 'notify-row';

      const sel = document.createElement('select');
      sel.className = 'notify-select';
      const noneOpt = document.createElement('option');
      noneOpt.value = '';
      noneOpt.textContent = '— keins (nur HA-Glocke) —';
      sel.appendChild(noneOpt);
      mobileServices.forEach(svc => {
        const opt = document.createElement('option');
        opt.value = svc;
        opt.textContent = svc.replace('mobile_app_', '').replace(/_/g, ' ');
        if (svc === this._config.notify_service) opt.selected = true;
        sel.appendChild(opt);
      });
      sel.addEventListener('change', e => {
        this._fire({ ...this._config, notify_service: e.target.value || undefined });
      });
      notifyRow.appendChild(sel);
      cfg.appendChild(notifyRow);
    }

    // Mode toggle: Auto / Manual
    const modeLbl = document.createElement('div');
    modeLbl.className = 'section-label';
    modeLbl.textContent = 'Haltestellen-Modus';
    cfg.appendChild(modeLbl);

    const isAuto = this._config.auto_entities !== false;
    const modeRow = document.createElement('div');
    modeRow.className = 'mode-row';
    ['Automatisch', 'Manuell'].forEach((label, i) => {
      const btn = document.createElement('button');
      btn.className = `mode-btn${(i === 0) === isAuto ? ' active' : ''}`;
      btn.textContent = label;
      btn.addEventListener('click', () => {
        this._fire({ ...this._config, auto_entities: i === 0 });
      });
      modeRow.appendChild(btn);
    });
    cfg.appendChild(modeRow);

    // Entity pickers — only in manual mode
    if (!isAuto) {
      const lbl = document.createElement('div');
      lbl.className = 'section-label';
      lbl.textContent = 'Haltestellen-Sensoren';
      cfg.appendChild(lbl);

      (this._config.entities || []).forEach((id, idx) => {
        cfg.appendChild(this._makeRow(id, idx));
      });

      const addBtn = document.createElement('button');
      addBtn.className = 'add-btn';
      addBtn.textContent = '+ Haltestelle hinzufügen';
      addBtn.addEventListener('click', () => {
        this._fire({ ...this._config, entities: [...(this._config.entities || []), ''] });
      });
      cfg.appendChild(addBtn);
    }

    // Line colors section
    const lines = this._collectLines();
    if (lines.length) {
      const colorLbl = document.createElement('div');
      colorLbl.className = 'section-label';
      colorLbl.textContent = 'Linienfarben';
      cfg.appendChild(colorLbl);

      lines.forEach(line => cfg.appendChild(this._makeColorRow(line)));
    }
  }

  _collectLines() {
    const lines = new Set();
    const ids = this._config.auto_entities !== false
      ? this._getVabEntities()
      : (this._config.entities || []);
    for (const id of ids) {
      const state = this._hass?.states[id];
      for (const dep of state?.attributes?.departures || []) {
        if (dep.line) lines.add(String(dep.line));
      }
    }
    return [...lines].sort((a, b) => (isNaN(a) || isNaN(b) ? a.localeCompare(b) : Number(a) - Number(b)));
  }

  _makeColorRow(line) {
    const currentColor = lineColor(line, this._config);
    const row = document.createElement('div');
    row.className = 'color-row';

    const badge = document.createElement('div');
    badge.className = 'color-badge';
    badge.style.background = currentColor;
    badge.textContent = line;

    const label = document.createElement('span');
    label.className = 'color-label';
    label.textContent = `Linie ${line}`;

    const input = document.createElement('input');
    input.type = 'color';
    input.className = 'color-input';
    input.value = currentColor;
    input.addEventListener('input', e => {
      badge.style.background = e.target.value;
    });
    input.addEventListener('change', e => {
      const colors = { ...(this._config.line_colors || {}), [line]: e.target.value };
      this._fire({ ...this._config, line_colors: colors });
    });

    const reset = document.createElement('button');
    reset.className = 'color-reset';
    reset.title = 'Auf Standard zurücksetzen';
    reset.textContent = '↺';
    reset.addEventListener('click', () => {
      const colors = { ...(this._config.line_colors || {}) };
      delete colors[line];
      this._fire({ ...this._config, line_colors: Object.keys(colors).length ? colors : undefined });
    });

    row.appendChild(badge);
    row.appendChild(label);
    row.appendChild(input);
    row.appendChild(reset);
    return row;
  }

  _makeRow(entityId, idx) {
    const row = document.createElement('div');
    row.className = 'entity-row';

    const picker = document.createElement('ha-entity-picker');
    picker.hass           = this._hass;
    picker.value          = entityId;
    picker.label          = `Sensor ${idx + 1}`;
    picker.includeEntities = this._getVabEntities();
    picker.addEventListener('value-changed', e => {
      const updated = [...(this._config.entities || [])];
      updated[idx] = e.detail.value;
      this._fire({ ...this._config, entities: updated });
    });

    const del = document.createElement('ha-icon-button');
    del.setAttribute('icon', 'mdi:delete');
    del.title = 'Entfernen';
    del.addEventListener('click', () => {
      const updated = [...(this._config.entities || [])];
      updated.splice(idx, 1);
      this._fire({ ...this._config, entities: updated });
    });

    row.appendChild(picker);
    row.appendChild(del);
    return row;
  }

  _fire(config) {
    this._config = config;
    this.dispatchEvent(new CustomEvent('config-changed', {
      detail: { config },
      bubbles: true,
      composed: true,
    }));
    this._build();
  }
}

// ─────────────────────────────────────────────
//  Styles
// ─────────────────────────────────────────────

const CARD_STYLES = `
  ha-card {
    overflow:hidden; padding:0;
    background: var(--vab-bg, var(--card-background-color));
    font-family: var(--vab-font, 'Fira Sans Condensed', 'Arial Narrow', sans-serif);
  }
  .card-header {
    padding: 16px 16px 0;
    font-size: 17px;
    font-family: var(--vab-header-font, var(--vab-font, inherit));
    font-weight: var(--vab-header-weight, 800);
    letter-spacing: var(--vab-header-tracking, .02em);
    text-transform: var(--vab-header-transform, none);
    color: var(--vab-header-color, var(--primary-text-color));
    margin: 0;
  }
  .stop-section { padding-bottom: 4px; }
  .stop-header {
    padding: 12px 16px 6px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: var(--vab-text-dim, var(--secondary-text-color));
  }
  .stop-header.collapsible {
    cursor: pointer;
    user-select: none;
  }
  .stop-header.collapsible:hover { color: var(--vab-text, var(--primary-text-color)); }
  .chevron { margin-right: 5px; font-size: 9px; }
  .collapsed-hint {
    padding: 2px 16px 8px;
    font-size: 11px;
    color: var(--vab-text-dim, var(--secondary-text-color));
  }
  .dir-label {
    font-weight: 400;
    text-transform: none;
    letter-spacing: 0;
  }
  .stop-divider {
    height: 0;
    border-top: 1px var(--vab-divider-style, solid) var(--vab-divider-color, var(--divider-color, #1a1a1a));
    margin: 4px 0;
  }
  .row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px;
    transition: background .1s;
  }
  .row:hover { background: var(--vab-row-hover-bg, var(--secondary-background-color)); }
  .dot {
    width: 7px; height: 7px;
    border-radius: var(--vab-dot-radius, 1px);
    flex-shrink: 0;
  }
  .dot.live    { background: var(--vab-dot-live, #1a3a5c); box-shadow: var(--vab-glow, none); }
  .dot.planned { background: var(--vab-dot-planned, var(--disabled-color, #9ca3af)); }
  .badge {
    min-width: 32px; height: 24px;
    border-radius: var(--vab-badge-radius, 2px);
    border: var(--vab-badge-border, 1.5px solid var(--line-color));
    background: var(--vab-badge-bg, transparent);
    color: var(--vab-badge-color, var(--line-color));
    font-size: 13px; font-weight: var(--vab-badge-weight, 800);
    display: flex; align-items: center; justify-content: center;
    padding: 0 5px;
    flex-shrink: 0;
    letter-spacing: .02em;
  }
  .starred-row { border-left: 3px solid var(--vab-warn, #b8860b); padding-left: 13px; }
  .row-star {
    background: none; border: none; cursor: pointer; padding: 0 0 0 6px;
    font-size: 14px; line-height: 1;
    color: var(--vab-text-dim, var(--secondary-text-color));
    flex-shrink: 0;
    opacity: 0.35;
    transition: opacity .15s, color .15s;
  }
  .row:hover .row-star { opacity: 0.75; }
  .row-star.starred { color: var(--vab-warn, #b8860b); opacity: 1; }
  .middle {
    flex: 1; min-width: 0;
    display: flex; flex-direction: column; gap: 1px;
  }
  .direction {
    font-size: 15px;
    font-weight: var(--vab-direction-weight, 500);
    color: var(--vab-text, var(--primary-text-color));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .platform { font-size: 11px; color: var(--vab-text-dim, var(--secondary-text-color)); }
  .time-col {
    text-align: right;
    flex-shrink: 0;
    display: flex; flex-direction: column; align-items: flex-end; gap: 1px;
  }
  .mins {
    font-size: 18px; font-weight: var(--vab-mins-weight, 700);
    font-variant-numeric: tabular-nums;
    color: var(--vab-text, var(--primary-text-color));
    line-height: 1.1;
  }
  .mins.now, .now-row .mins {
    color: var(--vab-mins-now, #c0272d);
    text-shadow: var(--vab-text-glow, none);
    animation: var(--vab-blink, none);
  }
  .clock-time {
    font-size: 11px;
    color: var(--vab-text-dim, var(--secondary-text-color));
    letter-spacing: .02em;
  }
  .delay       { font-size: 11px; font-weight: 600; color: var(--vab-delay, #b8860b); animation: var(--vab-blink, none); }
  .delay.severe{ color: var(--vab-delay-severe, #c0272d); }
  .on-time     { font-size: 11px; color: var(--vab-ontime, #3f6b4f); font-weight: 600; }
  .no-dep, .empty {
    padding: 8px 16px 12px;
    font-size: 13px;
    color: var(--vab-text-dim, var(--secondary-text-color));
  }
  .leave-now {
    border-left: 3px solid var(--vab-warn, #b8860b);
    padding-left: 13px;
    background: var(--vab-row-hover-bg, var(--secondary-background-color));
  }
  .leave-badge {
    font-size: 10px;
    font-weight: 700;
    color: var(--vab-warn, #b8860b);
    letter-spacing: .04em;
    text-transform: uppercase;
    animation: var(--vab-blink, leavePulse 1.2s ease-in-out infinite);
  }
  @keyframes leavePulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: .35; }
  }
  @keyframes vabBlink {
    50% { opacity: .25; }
  }
  .leave-soon {
    font-size: 10px;
    font-weight: 600;
    color: var(--vab-text-dim, var(--secondary-text-color));
    letter-spacing: .02em;
  }
  .next-day-badge {
    font-size: 10px;
    font-weight: 700;
    color: var(--vab-nextday, #c0272d);
    letter-spacing: .04em;
    text-transform: uppercase;
  }
`;

const EDITOR_STYLES = `
  .cfg { padding: 16px; display: flex; flex-direction: column; gap: 8px; }
  .section-label {
    font-size: 12px; font-weight: 600;
    color: var(--secondary-text-color);
    text-transform: uppercase; letter-spacing: .05em;
    margin-top: 4px;
  }
  .notify-hint {
    font-size: 11px; color: var(--secondary-text-color); margin-bottom: 2px;
  }
  .notify-row { display: flex; }
  .notify-select {
    flex: 1; padding: 8px 10px; border-radius: 6px;
    border: 1px solid var(--divider-color, #e5e7eb);
    background: var(--card-background-color);
    color: var(--primary-text-color);
    font-size: 14px; cursor: pointer;
  }
  .entity-row {
    display: flex; align-items: center; gap: 8px;
  }
  .entity-row ha-entity-picker { flex: 1; }
  .mode-row {
    display: flex; gap: 8px; margin-bottom: 8px;
  }
  .mode-btn {
    flex: 1; padding: 8px;
    border: 1px solid var(--divider-color, #ccc);
    border-radius: 6px;
    background: none;
    color: var(--primary-text-color);
    cursor: pointer; font-size: 13px;
    transition: background .15s, color .15s;
  }
  .mode-btn.active {
    background: var(--primary-color);
    color: #fff;
    border-color: var(--primary-color);
  }
  .add-btn {
    margin-top: 4px;
    background: none;
    border: 1px dashed var(--primary-color);
    color: var(--primary-color);
    border-radius: 6px;
    padding: 8px 12px;
    cursor: pointer;
    font-size: 13px;
    width: 100%;
  }
  .add-btn:hover { background: var(--primary-color); color: white; }
  .color-row {
    display: flex; align-items: center; gap: 10px;
    padding: 4px 0;
  }
  .color-badge {
    min-width: 34px; height: 26px;
    border-radius: 6px;
    color: #fff;
    font-size: 12px; font-weight: 800;
    display: flex; align-items: center; justify-content: center;
    padding: 0 6px;
    flex-shrink: 0;
  }
  .color-label { flex: 1; font-size: 13px; color: var(--primary-text-color); }
  .color-input {
    width: 36px; height: 28px;
    border: none; border-radius: 6px;
    padding: 2px; cursor: pointer;
    background: none;
  }
  .color-reset {
    background: none; border: none;
    color: var(--secondary-text-color);
    cursor: pointer; font-size: 16px;
    padding: 2px 4px; border-radius: 4px;
  }
  .color-reset:hover { color: var(--primary-text-color); }
`;

// ─────────────────────────────────────────────
//  Registration
// ─────────────────────────────────────────────

customElements.define('vab-departures-card', VabDeparturesCard);
customElements.define('vab-departures-card-editor', VabDeparturesCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'vab-departures-card',
  name: 'VAB Departures Card',
  description: 'Real-time bus and train departures for VAB Aschaffenburg',
  preview: false,
});
