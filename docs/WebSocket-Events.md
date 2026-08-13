# WebSocket Events

The integration connects to the Mnemos backend's `/ws/events` endpoint to receive live state changes without waiting for the next poll. This is how the `Unknown faces` sensor stays accurate within a second or two of a new identify call landing an unknown crop in the inbox.

## What is pushed

| Mnemos event | Effect in HA |
| --- | --- |
| `inbox.new_face` | Coordinator requests refresh; `Unknown faces` sensor updates |
| `inbox.bulk_changed` | Same — covers `assign`, `mark-non-face`, `ignore` |
| `warmup.done` | Logged at debug; the next coordinator tick picks up the new model |
| `warmup.error` | Logged at debug; the `Model loaded` binary sensor reflects it |
| `reindex.*` | Logged; `Reindex progress` attribute on the model sensor updates within 1 s |

## Reconnect behaviour

The WebSocket connection auto-reconnects with exponential backoff (1 s → 60 s, capped). If the backend is down for 5 minutes, the integration will still be in sync the moment the backend comes back.

## Heartbeats

The client sends a WebSocket ping every 20 s; the server has a 20 s pong timeout. Either side closing due to a missed ping triggers a clean reconnect.

## Disabling

The WebSocket is part of `async_setup_entry` and runs for the lifetime of the config entry. There is no toggle — if you want to suppress the live updates, raise the coordinator's `scan_interval` option to a very high value (e.g. 600 s); the WS will still trigger a refresh, but the poll cadence will be slow.

## Authentication

`/ws/events` does **not** require an API key on the Mnemos side. The connection is unauthenticated. This is by design — it's how the HTML dashboard in Mnemos receives updates without each browser needing a key.
