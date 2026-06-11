<p align="center">
  <img src="logo.svg" alt="VAB Abfahrtsmonitor" width="120"/>
</p>

<p align="center">
  <a href="https://github.com/mxkissnr/ha-vab-integration/releases/latest">
    <img src="https://img.shields.io/github/v/tag/mxkissnr/ha-vab-integration?color=%2341bdf5&label=Version&style=flat-square" alt="Version"/>
  </a>
  <img src="https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-41bdf5?logo=home-assistant&style=flat-square" alt="HA Integration"/>
  <img src="https://img.shields.io/badge/HACS-Custom-orange?style=flat-square" alt="HACS Custom"/>
  <img src="https://img.shields.io/badge/Built%20with-Claude%20by%20Anthropic-D97706?style=flat-square" alt="Built with Claude"/>
  <img src="https://img.shields.io/badge/status-Work%20In%20Progress-orange?style=flat-square" alt="Work In Progress"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-blue?style=flat-square" alt="License GPL-3.0"/>
</p>

<h2 align="center">VAB Abfahrtsmonitor</h2>

<p align="center">
  Real-time bus and train departure times for the <strong>VAB region (Aschaffenburg)</strong> directly in Home Assistant.<br/>
  Powered by the <a href="https://bahnland-bayern.de">Bahnland Bayern EFA API</a> for buses/trams and DB/IRIS via marudor.de for trains.
</p>

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| 🚌 | **Live bus departures** | Real-time data from EFA Bahnland Bayern — covers all VAB bus/tram stops |
| 🚆 | **Live train departures** | DB/IRIS real-time data via marudor.de |
| ⏱️ | **Delay tracking** | Shows delay in minutes per departure; `MONITORED` status indicates live GPS tracking |
| 🔍 | **Line filter** | Show only specific bus lines (e.g. only line 1 and 3) |
| 🧭 | **Direction filter** | Show only departures towards a specific destination (e.g. Innenstadt or Hauptbahnhof) |
| 🔁 | **Multiple sensors** | Add the same stop multiple times with different filters — one sensor per direction |
| ⚙️ | **Options flow** | Edit filters and departure count after setup — no need to re-add |
| 🔄 | **60s update interval** | Coordinator refreshes every 60 seconds |

---

## 🚀 Installation

### Via HACS (recommended)

**Step 1 — Add this repository to HACS:**

<p>
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=mxkissnr&repository=ha-vab-integration&category=integration">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." height="40"/>
  </a>
</p>

Or manually: **HACS → Integrations → ⋮ → Custom repositories** → add `https://github.com/mxkissnr/ha-vab-integration` as **Integration**.

After installing via HACS, restart Home Assistant.

**Step 2 — Add the integration:**

<p>
  <a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=vab">
    <img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Open your Home Assistant instance and start setting up a new integration." height="40"/>
  </a>
</p>

Or manually: **Settings → Integrations → + Add integration → VAB Abfahrtsmonitor**.

### Manual installation

1. Copy `custom_components/vab/` into your HA config directory: `config/custom_components/vab/`
2. Restart Home Assistant
3. Add the integration via the button above or **Settings → Integrations → + Add integration**

---

## ⚙️ Configuration

The setup opens automatically after clicking the button above.

The setup has three steps:

### Step 1 — Choose data source and search stop

| Option | Description |
|---|---|
| **Bus / Tram (EFA)** | All VAB bus and tram stops in the Aschaffenburg area |
| **Train (DB / IRIS)** | Train stations, e.g. Aschaffenburg Hbf |

Enter the stop name (e.g. `Hensbachstraße` or `Aschaffenburg Hauptbahnhof`).

### Step 2 — Select stop and departure count

Choose the correct stop from the search results and set how many departures to display (1–20, default 5).

### Step 3 — Filter lines and directions (optional)

The integration fetches live departures and shows available lines and directions as checkboxes.

- **Line filter** — leave empty to show all lines; or select e.g. `Linie 1`, `Linie 3`
- **Direction filter** — leave empty to show all directions; or select e.g. `Innenstadt`

**Tip:** Add the same stop twice with different direction filters to get two separate sensors — one per direction.

---

## 📊 Sensor

Each configured stop creates one sensor entity.

**State:** Minutes until the next departure (real-time if monitored, otherwise planned).

**Attributes:**

| Attribute | Description |
|---|---|
| `next_line` | Line number of the next departure |
| `next_direction` | Destination of the next departure |
| `next_platform` | Platform / bay (if available) |
| `next_delay_minutes` | Delay in minutes (0 = on time) |
| `next_monitored` | `true` if the vehicle is live-tracked |
| `next_rt_status` | `MONITORED` or `PLANNED` |
| `departures` | Full list of upcoming departures (array) |
| `stop_id` | Internal EFA / EVA stop ID |
| `stop_name` | Human-readable stop name |
| `line_filter` | Active line filter (empty = all) |
| `direction_filter` | Active direction filter (empty = all) |
| `source` | `efa` or `db` |

Each entry in `departures` contains: `line`, `direction`, `platform`, `planned`, `realtime`, `effective`, `delay_minutes`, `minutes_until`, `monitored`, `rt_status`.

---

## 🃏 Example Lovelace card

```yaml
type: markdown
content: >
  ## 🚌 {{ state_attr('sensor.abfahrt_hensbachstrasse_innenstadt', 'next_line') }}
  → {{ state_attr('sensor.abfahrt_hensbachstrasse_innenstadt', 'next_direction') }}

  in **{{ states('sensor.abfahrt_hensbachstrasse_innenstadt') }} min**

  {% set delay = state_attr('sensor.abfahrt_hensbachstrasse_innenstadt', 'next_delay_minutes') %}
  {% if delay > 0 %}⚠️ +{{ delay }} min Verspätung{% else %}✅ Pünktlich{% endif %}

  {% if not state_attr('sensor.abfahrt_hensbachstrasse_innenstadt', 'next_monitored') %}
  _(kein Echtzeitsignal)_
  {% endif %}
```

---

## 🔄 Updating filters after setup

In **Settings → Integrations → VAB Abfahrtsmonitor → Configure** you can change:
- Which lines to show
- Which directions to show
- How many departures to display

The integration reloads live departure data each time you open the options dialog.

---

## 📡 Data sources

| Source | API | Coverage |
|---|---|---|
| EFA Bahnland Bayern | `https://bahnland-bayern.de/efa/` | All VAB bus/tram stops in Aschaffenburg and surroundings |
| DB / IRIS (marudor.de) | `https://marudor.de/api/iris/v2/abfahrten/` | Train stations in Germany |

Both APIs are free and require no API key.

---

## 📝 License

GPL-3.0 — see [LICENSE](LICENSE)
