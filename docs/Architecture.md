# Architecture

Mnemos-HA is a single HACS custom integration under `custom_components/mnemos/`. There is one config entry per backend; multiple backends are supported in state, but `mnemos.identify` resolves to the first one.

## Module map

```
custom_components/mnemos/
├── __init__.py        # async_setup_entry: client + coordinator + WS task + state
├── api.py             # aiohttp wrapper: healthz, model_info, unassigned_total, identify
├── coordinator.py     # DataUpdateCoordinator: polls health/model/inbox on a timer
├── events.py          # WebSocket task: re-uses aiohttp session, exponential backoff
├── sensor.py          # 6 entities: Model, Last identify, Status, Variant, Model loaded, Unknown faces
├── binary_sensor.py   # 1 entity: Reachable
├── services.py        # mnemos.identify + mnemos.refresh
├── config_flow.py     # UI setup + options flow
├── diagnostics.py     # Redacted dump for the HA diagnostics panel
├── exceptions.py      # Typed errors for the api layer
├── state.py           # MnemosEntryState: client, coordinator, last_identify, ws_task
└── const.py           # All string literals as Final
```

## Data flow

### 1. Setup

```
ConfigFlow validates against /healthz
   → MnemosClient (aiohttp session + base_url)
   → MnemosCoordinator (DataUpdateCoordinator; first refresh)
   → MnemosEntryState stored in hass.data[DOMAIN][entry_id]
   → WebSocket task started on the HA event loop
   → Platforms (binary_sensor, sensor) registered
   → Services (identify, refresh) registered on first entry only
```

### 2. Coordinator refresh

```
every scan_interval (default 30 s):
   asyncio.gather(
       client.healthz(),
       client.model_info(),
       client.unassigned_total(),   # GET /api/v1/faces/unassigned?count_only=true
   )
   → { health, model, inbox } → all sensors read this dict
```

### 3. WebSocket push

```
events.watch_backend_events (background task):
   aiohttp session.ws_connect(client.ws_url)
   on TEXT message:
     if type in (inbox.new_face, inbox.bulk_changed):
       coordinator.async_request_refresh()
   on disconnect:
     sleep 1→2→4→…→60 s, retry
```

### 4. Identify action

```
mnemos.identify service:
   read source (camera.* latest still | file_path on disk)
   POST /api/v1/identify (multipart/form-data)
   response → { persons, unknown, took_ms } → MnemosEntryState.last_identify
   last_identify_listeners[].cb() → Last identify sensor writes state
```

## Why one coordinator and one WS task per entry

The WebSocket is per-backend — you can't share it across entries because each has its own host/port. The coordinator is also per-entry because it holds the `MnemosClient` and the cached `data` dict. If you want to monitor two backends, add the integration twice.

## Why `count_only=true` for the inbox

The default `GET /api/v1/faces/unassigned?page=1&page_size=1` still materialises the full unassigned list server-side and just slices the first item. On a 10k-crop inbox that's wasteful. The `count_only=true` query param returns `{total, page: 1, page_size: 0, items: []}` after a single `COUNT(*)`, which the coordinator polls.

## Why no `data_class` on the Last identify sensor

The sensor's `native_value` is a formatted string (`"Alice (91%)"`), not a number. Using `SensorStateClass.MEASUREMENT` would mislead long-term statistics. The `extra_state_attributes` carry the structured data for automations.
