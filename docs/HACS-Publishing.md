# HACS Publishing

This document covers what HACS checks before accepting a release and the conventions to follow so submissions pass on the first try.

## Required files at the repo root

| File | Purpose |
| --- | --- |
| `hacs.json` | Tells HACS the minimum HA version, render mode, supported countries |
| `info.md` | Short blurb shown in the HACS store |
| `README.md` | Full documentation (HACS renders this with `render_readme: true`) |
| `LICENSE` | MIT or compatible; HACS rejects without one |
| `custom_components/<domain>/manifest.json` | Integration manifest with `domain`, `name`, `version`, `config_flow`, `iot_class`, `codeowners`, `requirements` |

## `hacs.json` — what HACS validates

```json
{
  "name": "Mnemos",
  "homeassistant": "2025.1.0",
  "render_readme": true,
  "country": ["GB", "US", "AU", "CA", "DE", "FR", "IN", "ZA", "IE", "NZ"]
}
```

- `name` must match `manifest.json`'s `name`.
- `homeassistant` is the **minimum** HA version. Don't set it below what your code actually requires.
- `render_readme` should be `true` unless you want to display `info.md` instead.
- `country` is optional but useful for the HACS store filter.

## `manifest.json` — what HACS validates

Required keys:

- `domain` — must match the folder name (`mnemos`).
- `name` — display name (≤ 64 chars).
- `version` — SemVer string. **Bump on every release** or HACS won't show the update.
- `config_flow` — `true` for UI-configurable integrations.
- `codeowners` — list of GitHub handles.
- `iot_class` — one of `local_polling`, `local_push`, `cloud_polling`, `cloud_push`. We use `local_polling` because the coordinator polls on a timer (the WebSocket is a fast-path, not a replacement).
- `integration_type` — `service` for action-style integrations like ours, or `device` / `hub`.
- `requirements` — list of PyPI packages with version pins. aiohttp is already in HA core, but a pin doesn't hurt.

## Pre-release checklist

- [ ] `manifest.json` `version` is bumped.
- [ ] `README.md` "Features" and "Examples" reflect any new entities/services.
- [ ] `docs/` has a page for any new entity.
- [ ] `tests/` cover any new code path.
- [ ] `ruff check .` and `pytest tests/` pass.
- [ ] `git tag v1.x.y` is pushed.

## Submitting a release

```bash
git tag v1.2.3
git push origin v1.2.3
# then: GitHub → Releases → Draft a new release → choose the tag → Publish
```

HACS picks up new releases within ~15 minutes.
