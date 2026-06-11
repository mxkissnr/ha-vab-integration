# Changelog

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
