# Changelog

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
