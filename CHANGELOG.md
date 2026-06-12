# Changelog

## v2.0.0 — 2026-06-12

### Breaking Change
- **DB/IRIS (Zug via marudor.de) komplett entfernt** — die Integration fokussiert sich ausschließlich auf VAB Bus/Tram via EFA Bahnland Bayern. Bestehende DB/IRIS-Konfigurationen werden nicht mehr geladen und müssen entfernt werden. Für Züge gibt es bessere dedizierte HA-Integrationen ([#16](https://github.com/mxkissnr/ha-vab-integration/issues/16))

### Changed
- Setup-Flow Schritt 1: Quellauswahl (Bus/Zug) entfernt — direkt Haltestellen-Suche
- `CONF_SOURCE`, `SOURCE_EFA`, `SOURCE_DB`, `MARUDOR_*` Konstanten entfernt
- `api.py`: `db_stop_search`, `db_fetch_raw` entfernt
- `coordinator.py`: `_fetch_db`, `_parse_db`, `_parse_iso_ms` entfernt

## v1.5.0 — 2026-06-11

### Added
- **Options take effect immediately** — adding `update_listener` in `async_setup_entry` so filter/walk-time changes via the options flow reload the coordinator instantly, no HA restart needed ([#12](https://github.com/mxkissnr/ha-vab-integration/issues/12))
- **Unit tests** — `tests/test_utils.py` (normalize_direction, sort_lines) and `tests/test_coordinator.py` (_apply_filters, _parse_efa, _parse_db) with HA-module stubs so tests run without a full HA install ([#13](https://github.com/mxkissnr/ha-vab-integration/issues/13))

### Changed
- `CLAUDE.md` extended with full architecture reference, both repo paths, sensor attributes, and card config — usable from any machine without prior session context

## v1.4.0 — 2026-06-11

### Changed
- **Architecture refactor** — all HTTP calls extracted into `api.py` (`efa_stop_search`, `db_stop_search`, `efa_fetch_raw`, `db_fetch_raw`, `efa_line_directions`); string helpers in `utils.py` (`normalize_direction`, `sort_lines`). Eliminates duplicate `_normalize_direction`/`_normalize_dir` functions and the duplicated `_load_filter_options` method that existed in both `VabConfigFlow` and `VabOptionsFlow` ([#10](https://github.com/mxkissnr/ha-vab-integration/issues/10))
- `config_flow.py` now uses limit=60 (was 30) when fetching lines/directions for the setup wizard — consistent with the options flow

## v1.3.0 — 2026-06-11

### Changed
- Setup and options flow split into two direction steps: **Step 1** selects lines + walk time, **Step 2** shows only the directions actually served by those lines — no more direction list cluttered with irrelevant lines ([#9](https://github.com/mxkissnr/ha-vab-integration/issues/9))

## v1.2.0 — 2026-06-11

### Added
- **Walk time** — configure walking time to the stop (0–30 min) in setup and options. Each departure gets a `leave_in_minutes` attribute (`minutes_until - walk_time`). Enables automations: "notify when `leave_in_minutes ≤ 2`" ([#6](https://github.com/mxkissnr/ha-vab-integration/issues/6))
- **Cancelled departures filtered** — trips with `realtimeTripStatus: CANCELLED` are now skipped ([#8](https://github.com/mxkissnr/ha-vab-integration/issues/8))

### Fixed
- **Direction normalization** — EFA's inconsistent formatting ("Aschaffenburg ; HBF/ROB", "HBF / ROB", "Hbf/ROB") is now normalized so duplicates no longer appear in the direction filter list ([#7](https://github.com/mxkissnr/ha-vab-integration/issues/7))

## v1.1.2 — 2026-06-11

### Changed
- All HTTP requests now send a `User-Agent` header identifying the integration — good practice so API operators can see who is querying

## v1.1.1 — 2026-06-11

### Fixed
- Overnight lookahead: fetch limit increased to 100 (was 30) so busy stops with many lines still find the filtered line in the result; added second retry at 05:00 if midnight fetch is empty ([#4](https://github.com/mxkissnr/ha-vab-integration/issues/4))

## v1.1.0 — 2026-06-11

### Added
- Overnight lookahead for EFA: when no departures are found for the current time window (e.g. after the last bus at night), the coordinator automatically retries with the next day's schedule so the sensor always shows when the next bus comes ([#4](https://github.com/mxkissnr/ha-vab-integration/issues/4))
- DB/IRIS: extended lookahead to 480 min (was 120), with automatic retry at 1440 min if still empty

## v1.0.2 — 2026-06-11

### Fixed
- Options flow and step 3 filter selectors not appearing when EFA API returns `"departureList": null` — same null-bug as #1 was also present in both `_load_filter_options` methods in `config_flow.py`, causing a TypeError that silently left the available lines/directions empty ([#3](https://github.com/mxkissnr/ha-vab-integration/issues/3))

## v1.0.1 — 2026-06-11

### Fixed
- Sensor showing **Unknown** when EFA API returns `"departureList": null` — `get()` default was not applied for null values, causing a TypeError in the coordinator ([#1](https://github.com/mxkissnr/ha-vab-integration/issues/1))
- Added warning log when departures are fetched but all filtered out by line/direction filter, showing available directions to help fix misconfigured filters

## v1.0.0 — 2026-06-11

### Added
- Initial release
- EFA Bahnland Bayern integration for real-time bus/tram departures (VAB Aschaffenburg)
- DB/IRIS integration via marudor.de for real-time train departures
- 3-step config flow: stop search → stop selection → line/direction filter
- OptionsFlow: edit filters and max departures after initial setup
- Line filter (exact match) and direction filter (case-insensitive substring match)
- Real-time delay fields: `delay_minutes`, `monitored`, `rt_status` per departure
- `next_delay_minutes`, `next_monitored` as top-level sensor attributes for easy Lovelace access
- Platform field (`next_platform`) from EFA response
- DE + EN translations
- HACS-compatible structure
