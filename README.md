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
  Real-time bus and tram departure times for the <strong>VAB region (Aschaffenburg)</strong> directly in Home Assistant.<br/>
  Powered by the <a href="https://bahnland-bayern.de">Bahnland Bayern EFA API</a>.
</p>

<p align="center">
  Pair with the <a href="https://github.com/mxkissnr/vab-departures-card"><strong>VAB Departures Card</strong></a> for a full departure board in your Lovelace dashboard.
</p>

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| 🚌 | **Live bus/tram departures** | Real-time data from EFA Bahnland Bayern — covers all VAB bus/tram stops |
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

The setup has four steps:

### Step 1 — Search stop

Enter the stop name (e.g. `Freihofsplatz` or `Hensbachstraße`).

### Step 2 — Select stop and departure count

Choose the correct stop from the search results and set how many departures to display (1–20, default 5).

### Step 3 — Filter lines and walk time (optional)

- **Line filter** — leave empty to show all lines; or select e.g. `Linie 1`, `Linie 3`
- **Walk time** — walking time in minutes from your home to this stop (0–30). Enables `leave_in_minutes` per departure so you know when to leave, not just when the bus departs.

### Step 4 — Filter directions (optional)

Only shows directions served by the lines selected in Step 3.

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
| `walk_time` | Configured walk time to the stop in minutes |
| `source` | always `efa` |

Each entry in `departures` contains: `line`, `direction`, `platform`, `planned`, `realtime`, `effective`, `delay_minutes`, `minutes_until`, `leave_in_minutes` (= `minutes_until − walk_time`, only when walk_time > 0), `monitored`, `rt_status`, `source`.

---

## 🃏 Lovelace card

Use the dedicated **[VAB Departures Card](https://github.com/mxkissnr/vab-departures-card)** for a full departure board — auto-detects all VAB sensors, live countdown, walk-time alerts, star notifications, and push notifications to your phone.

---

## 🔄 Updating filters after setup

In **Settings → Integrations → VAB Abfahrtsmonitor → Configure** you can change:
- Which lines to show
- Which directions to show
- How many departures to display

The integration reloads live departure data each time you open the options dialog.

---

## 📡 Data source

**EFA Bahnland Bayern** — `https://bahnland-bayern.de/efa/` — free, no API key required.

Operated by the [Bayerische Eisenbahngesellschaft (BEG)](https://www.beg.bahnland-bayern.de), a public authority funded by the Bavarian state. The EFA (Elektronische Fahrplanauskunft) system is the standard trip planning and departure monitor backbone for public transport in Bavaria.

Real-time data comes from the **AVMS** (Automatic Vehicle Monitoring System) — buses send GPS positions which EFA uses to calculate precise arrival/departure times at all downstream stops. When a departure shows `MONITORED`, its times are live GPS-based. `PLANNED` means schedule only (no GPS signal).

### Usage & rate limiting

This integration queries each configured stop every **60 seconds**. Each sensor generates one API request per update cycle. The integration sends a `User-Agent` header (`ha-vab-integration`) so operators can identify the traffic source.

---

## 📝 License

GPL-3.0 — see [LICENSE](LICENSE)
