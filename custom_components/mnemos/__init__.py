from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MnemosClient
from .const import (
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USE_SSL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import MnemosCoordinator
from .events import safe_close, watch_backend_events
from .services import async_register_services, async_unregister_services
from .state import MnemosEntryState

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = MnemosClient(
        session,
        host=entry.data["host"],
        port=entry.data[CONF_PORT],
        api_key=entry.data["api_key"],
        use_ssl=entry.data.get(CONF_USE_SSL, False),
    )

    scan_interval = int(
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    coordinator = MnemosCoordinator(hass, client, scan_interval)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(str(err)) from err

    stop_event = asyncio.Event()
    state = MnemosEntryState(client=client, coordinator=coordinator)
    state.stop_event = stop_event
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = state

    ws_task = hass.loop.create_task(
        watch_backend_events(hass, client, coordinator, stop_event)
    )
    state.ws_task = ws_task

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.data[DOMAIN].get("_services_registered"):
        async_register_services(hass)
        hass.data[DOMAIN]["_services_registered"] = True

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    state = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if state is not None and getattr(state, "stop_event", None) is not None:
        state.stop_event.set()
    if state is not None and getattr(state, "ws_task", None) is not None:
        await safe_close(state.ws_task)

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data[DOMAIN]:
        async_unregister_services(hass)
    return unloaded


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
