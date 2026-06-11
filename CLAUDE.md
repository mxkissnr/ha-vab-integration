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

## Repo structure

```
custom_components/vab/     ← HA custom integration
  __init__.py              ← async_setup_entry / async_unload_entry
  manifest.json            ← domain, version, iot_class
  const.py                 ← all constants, API URLs, CONF_* keys
  coordinator.py           ← DataUpdateCoordinator, EFA + DB parsers, filter logic
  config_flow.py           ← 3-step UI flow + OptionsFlow
  sensor.py                ← VabDepartureSensor entity
  strings.json             ← German strings (HA fallback)
  translations/
    de.json                ← German translations
    en.json                ← English translations
hacs.json                  ← HACS metadata
CHANGELOG.md
README.md
```

## Key conventions

- **EFA base URL:** `https://bahnland-bayern.de/efa` — covers all VAB bus/tram stops in Aschaffenburg
- **DB/IRIS base URL:** `https://marudor.de/api` — real-time trains, EVA number as stop ID
- **Stop IDs:** EFA returns numeric IDs (e.g. `80029009`) as `stateless` field in stop finder response
- **Real-time fields:** `realtimeTripStatus == "MONITORED"` means live-tracked; `servingLine.delay` is delay in minutes (string); `realDateTime` is the actual departure time
- **Direction filter:** substring match (case-insensitive) so "Hbf" matches "Aschaffenburg, Hauptbahnhof"
- **Line filter:** exact match on `servingLine.number`
- **Fetch limit:** always fetch `max_departures * 4` (min 30) so filters still leave enough results
- **Coordinator update interval:** 60 seconds
