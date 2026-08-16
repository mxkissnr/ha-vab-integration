# CLAUDE.md — HA VAB Integration

Working rules for this repo. Follow these in every session.

## Language rules

- **Code, comments, commit messages, GitHub issues, PR descriptions** → always English
- **README.md** → English (primary)
- **HA translations** → `translations/de.json` (German) + `translations/en.json` (English); always keep both in sync
- **strings.json** → German (HA default, used as fallback)

## Workflow

> **STOP — issue first, then code.**
> Do not write a single line of implementation before the issue exists.
> No exceptions for bug fixes, refactors, or "small" changes.
> The only exception is a typo or single-word change.

**Step 1 — create the issue (always, before anything else):**
```
gh issue create --repo mxkissnr/ha-vab-integration --title "..." --label "bug|enhancement" --body "..."
```

**Step 2 — implement the fix/feature.**

**Step 3 — close the issue in the commit message:** `Closes #N`

## Versioning

- Patch fix → bump third number: `1.0.0 → 1.0.1`
- New feature → bump second number: `1.0.1 → 1.1.0`
- Breaking change (config schema change) → bump first number

Always update **both**:
- `custom_components/vab/manifest.json` → `"version"`
- `CHANGELOG.md` → new entry at the top

## Commits

Every commit that ships a feature or fix needs:
1. Code change
2. `CHANGELOG.md` entry at the top
3. `translations/de.json` **and** `translations/en.json` update if UI-facing — always in sync
4. `manifest.json` version bump

After the commit:
```
git tag v<version>
git push origin main
git push origin v<version>
gh release create v<version> --title "v<version>" --notes "..."
```

## Repos

- **Integration:** `github.com/mxkissnr/ha-vab-integration` — local `/home/mk/Dokumente/Projekte/ha-vab-integration`
- **Lovelace Card:** `github.com/mxkissnr/vab-departures-card` — local `/home/mk/Dokumente/Projekte/vab-departures-card`

The card is a separate repo with its own CHANGELOG.md and git tags. Card issues go to `--repo mxkissnr/vab-departures-card`.

## Repo structure

```
custom_components/vab/     ← HA custom integration
  __init__.py              ← async_setup_entry / async_unload_entry + update listener
  manifest.json            ← domain, version, iot_class
  const.py                 ← all constants, API URLs, CONF_* keys
  api.py                   ← all HTTP calls: efa_stop_search, db_stop_search,
                              efa_fetch_raw, db_fetch_raw, efa_line_directions
  utils.py                 ← normalize_direction, sort_lines
  coordinator.py           ← VabCoordinator (DataUpdateCoordinator)
                              _parse_efa / _parse_db / _apply_filters (pure functions)
  config_flow.py           ← VabConfigFlow (4 steps) + VabOptionsFlow (2 steps)
                              shared helpers: _directions_for_lines, _build_entry_title
  sensor.py                ← VabDepartureSensor entity
  watches.py               ← WatchManager: server-side departure watches (star notifications),
                              persisted via homeassistant.helpers.storage.Store
  services.yaml            ← vab.watch_departure / vab.unwatch_departure service schemas
  strings.json             ← German strings (HA fallback)
  translations/
    de.json                ← German translations
    en.json                ← English translations
tests/
  test_utils.py            ← normalize_direction, sort_lines
  test_coordinator.py      ← _parse_efa, _parse_db, _apply_filters
hacs.json                  ← HACS metadata
CHANGELOG.md
README.md
```

## Config flow steps

1. **user** — source (EFA/DB) + stop search
2. **select_stop** — pick stop + max departures
3. **filters** — line filter (multi-select) + walk time (0–30 min)
4. **directions** — direction filter, pre-filtered to selected lines

OptionsFlow: **init** (lines + max departures + walk time) → **directions**

## Key conventions

- **EFA base URL:** `https://bahnland-bayern.de/efa` — covers all VAB bus/tram stops in Aschaffenburg
- **DB/IRIS base URL:** `https://marudor.de/api` — real-time trains, EVA number as stop ID
- **Stop IDs:** EFA returns numeric IDs (e.g. `80029009`) as `stateless` field in stop finder response
- **Real-time fields:** `realtimeTripStatus == "MONITORED"` means live-tracked; `servingLine.delay` is delay in minutes (string); `realDateTime` is the actual departure time
- **Direction filter:** substring match (case-insensitive) so "Hbf" matches "Aschaffenburg, Hauptbahnhof"
- **Line filter:** exact match on `servingLine.number`
- **Fetch limit:** always fetch `max_departures * 4` (min 30) so filters still leave enough results
- **Overnight lookahead (EFA):** retry with next day `itdDate=YYYYMMDD&itdTime=0000`, then `0500` if still empty
- **DB lookahead:** try 480 min, retry 1440 min if empty
- **Coordinator update interval:** 60 seconds
- **Coordinator reload:** `entry.add_update_listener(async_reload_entry)` in `async_setup_entry` — options changes take effect immediately without HA restart
- **`departureList: null`:** always use `data.get("departureList") or []` (never `.get(..., [])`) — the API returns null, not missing key

## Server-side watches

`watches.py` — `WatchManager` holds all watches across config entries, persisted via `Store`. A
watch = `{entry_id, line, direction, planned, notify_service, leave_threshold}` + server-side
notified-state (`notified_leave`, `notified_delay`). Registered once per `hass` instance in
`__init__.py` (not per entry), in `hass.data[DOMAIN]["_watch_manager"]`.

Services `vab.watch_departure` / `vab.unwatch_departure` (see `services.yaml`) resolve
`entity_id` → `entry_id` via the entity registry. `coordinator.py` calls
`watch_manager.async_check(entry_id, stop_name, result)` after every update — leave
notification fires once when `leave_in_minutes <= leave_threshold` (re-arms when back above),
delay notification fires when the delay value changes (re-arms at 0). Notifications go to the
watch's `notify_service` if it exists under `notify.*`, else the HA persistent notification
bell. Watches auto-expire once their departure has passed and left the data.

## Sensor attributes

Top-level: `next_line`, `next_direction`, `next_platform`, `next_delay_minutes`, `next_monitored`, `stop_name`, `line_filter`, `direction_filter`, `walk_time`, `watched`, `source`

Per departure in `departures[]`: `line`, `direction`, `platform`, `planned`, `realtime`, `effective`, `delay_minutes`, `minutes_until`, `leave_in_minutes` (= minutes_until − walk_time, only when walk_time > 0), `monitored`, `rt_status`, `source`

## Lovelace card

Single JS file `vab-departures-card.js` in separate repo. Config:

```yaml
type: custom:vab-departures-card
title: Meine Haltestellen
entities:
  - sensor.vab_freihofsplatz
leave_threshold: 2        # highlight row when leave_in_minutes <= this (default 2)
line_colors:
  "10": "#f97316"
  "4":  "#2563eb"
```

Features: colored line badges, minutes countdown, clock time, delay (amber/red), live dot, "Jetzt los!" indicator (orange pulsing badge when `leave_in_minutes <= leave_threshold`), visual editor with entity picker + color pickers.
