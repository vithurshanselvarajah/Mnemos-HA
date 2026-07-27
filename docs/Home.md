# Mnemos-HA Wiki

> Pronounced **nee-MOZ** — Greek goddess of memory.

Mnemos-HA is the official [HACS](https://hacs.xyz/) integration for the [Mnemos](https://github.com/vithurshan-selvarajah/Mnemos) face-recognition backend. It lets Home Assistant send a snapshot from a `camera.*` entity (or any local image) to Mnemos and react to the identified person(s) in any automation.

This wiki is the canonical documentation for the integration. It syncs from the `docs/` folder in the [main repository](https://github.com/vithurshan-selvarajah/Mnemos-HA). If you find something missing or wrong, please open an issue.

---

## I just want to install it

1. [Installation](../README.md#installation) — HACS or manual copy; restart HA.
2. [Configuration](../README.md#configuration) — host, port, API key, options.
3. [Quick example](../README.md#quick-example) — `mnemos.identify` from a camera in one automation.

## I want to use it from automations

4. [The `mnemos.identify` action](../README.md#mnemosidentify-action) — fields, response shape, return variable.
5. [Examples](../README.md#examples) — door greeting, doorbell snapshot, "skip when down", reindex progress.
6. [Troubleshooting](../README.md#troubleshooting) — auth errors, connection errors, no matches.

## I want to extend it

7. [Entities](../README.md#features) — every sensor and binary sensor, with attributes.
8. [Services](../README.md#mnemosidentify-action) — `mnemos.identify` and `mnemos.refresh`.
9. [API key permissions](API-Keys.md) — Identify-Only vs. Full-Admin; what works for which feature.
10. [WebSocket push](WebSocket-Events.md) — how the integration stays in sync with the backend without polling.

## I want to develop it

11. [Architecture](Architecture.md) — coordinator, sensors, state, services, WebSocket task.
12. [Testing](Testing.md) — how the test suite is structured; how to run it.
13. [HACS publishing](HACS-Publishing.md) — what HACS checks before accepting a release; version bumps.
14. [Contributing](../README.md#license) — PR conventions, code style, debugging.

---

## Project at a glance

- **Stack** — Python ≥ 3.12, aiohttp, Home Assistant `core` 2025.1+
- **License** — MIT. See [LICENSE](../LICENSE).
- **HACS** — Custom integration (no default repo). Add `vithurshan-selvarajah/Mnemos-HA` as a custom repository under **Integration**.

## How to read this wiki

Every page follows the same shape:

1. **What this is** — a one-paragraph summary.
2. **How to do the common thing** — copy-pasteable examples.
3. **For developers** — internals, knobs, gotchas.

If you only read sections 1 and 2 you can install and use the integration. Section 3 is for when something breaks or you're contributing.
