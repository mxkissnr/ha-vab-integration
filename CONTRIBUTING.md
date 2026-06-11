# Contributing

Bug reports, feature ideas and pull requests are welcome!

## Workflow

1. **Open an issue first** — describe the bug or feature before writing any code  
   (no PRs without a linked issue — see [CLAUDE.md](CLAUDE.md) for context)
2. **Fork & branch** — `feature/short-description` or `fix/short-description`
3. **Implement** — commit with `Closes #N` in the message
4. **Pull request** — reference the issue; keep PRs focused on one thing

## Reporting a bug

Include:
- Integration version (visible in Settings → Integrations)
- Home Assistant version
- Expected vs. actual behaviour
- Relevant log output (`Settings → System → Logs`, filter by `vab`)

## Code notes

| Area | Details |
|---|---|
| Coordinator | `coordinator.py` — fetches EFA/DB, applies filters, parses departure data |
| Config flow | `config_flow.py` — 3-step setup + OptionsFlow for editing |
| Sensor | `sensor.py` — exposes `minutes_until` as state, full departure list as attributes |
| Constants | `const.py` — all API URLs and `CONF_*` keys live here |
| Translations | `translations/de.json` + `translations/en.json` — always update both together |

## Versioning

`MAJOR.MINOR.PATCH` — patch for fixes, minor for new features, major for breaking config schema changes.  
Always bump `manifest.json` version **and** add a `CHANGELOG.md` entry in the same commit.
