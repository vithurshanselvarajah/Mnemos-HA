# Testing

The integration has a `pytest` test suite under `tests/`. It runs without a live Home Assistant install by stubbing out the HA core.

## Running

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-test.txt
pip install -e .
pytest tests/ -v
```

## Layout

```
tests/
├── conftest.py                # fake hass + session + ConfigEntry fixtures
├── test_api.py                # MnemosClient: healthz, identify, unassigned_total
├── test_coordinator.py        # success + auth/connection failure
├── test_events.py             # ws reconnect + event dispatch
├── test_sensor.py             # each sensor's native_value + extra_state_attributes
├── test_binary_sensor.py      # reachable + missing vector_db
├── test_services.py           # mnemos.identify service schema + response
├── test_config_flow.py        # success, invalid_key, cannot_connect
└── test_state.py              # get_entry_state / resolve_entry_state errors
```

## Fixtures

- `fake_hass` — a stub `HomeAssistant`-like object that records `async_create_task` and `bus.async_listen`.
- `fake_session` — an `aiohttp` test session that matches `GET /healthz`, `GET /api/v1/models`, `GET /api/v1/faces/unassigned?count_only=true`, and `POST /api/v1/identify` to canned JSON.
- `config_entry` — a `MockConfigEntry` pre-populated with the standard test data.
- `ws_events` — a fake `aiohttp` WebSocket that yields a scripted sequence of `inbox.new_face` events.

## Adding a test

1. Add the fixture inputs to `conftest.py` if the new test needs HA APIs you haven't stubbed yet.
2. Keep the test unit-level: don't spin up a real HA, just patch the bits you need.
3. If the test exercises `aiohttp` HTTP, use the `aiohttp.test_utils` helpers to drive a test server on a random port.
4. If the test exercises a WebSocket, use `aiohttp.test_utils.TestServer` + `TestClient`.

## CI

`.github/workflows/ci.yml` (if present) runs `ruff check .` and `pytest tests/` on every push and PR.
