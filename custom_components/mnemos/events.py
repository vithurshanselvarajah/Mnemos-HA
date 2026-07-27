from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

import aiohttp
from aiohttp import ClientError, WSMsgType

from .api import MnemosClient
from .const import EVENT_INBOX_BULK_CHANGED, EVENT_INBOX_NEW_FACE
from .coordinator import MnemosCoordinator

_LOGGER = logging.getLogger(__name__)

_RECONNECT_INITIAL_DELAY = 1.0
_RECONNECT_MAX_DELAY = 60.0
_PING_INTERVAL = 20.0
_PING_TIMEOUT = 20.0
_OPEN_TIMEOUT = 10.0


async def watch_backend_events(
    hass,
    client: MnemosClient,
    coordinator: MnemosCoordinator,
    stop_event: asyncio.Event,
) -> None:
    delay = _RECONNECT_INITIAL_DELAY
    while not stop_event.is_set():
        try:
            await _run_one_session(client, coordinator, stop_event)
            delay = _RECONNECT_INITIAL_DELAY
        except asyncio.CancelledError:
            raise
        except Exception as err:
            _LOGGER.debug("ws events: session ended (%s); retrying in %.1fs", err, delay)
        if stop_event.is_set():
            break
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=delay)
        except TimeoutError:
            pass
        else:
            break
        delay = min(delay * 2.0, _RECONNECT_MAX_DELAY)


async def _run_one_session(
    client: MnemosClient,
    coordinator: MnemosCoordinator,
    stop_event: asyncio.Event,
) -> None:
    ws_url = client.ws_url
    _LOGGER.debug("ws events: connecting to %s", ws_url)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=_OPEN_TIMEOUT)
    async with client.session.ws_connect(
        ws_url,
        timeout=timeout,
        heartbeat=_PING_INTERVAL,
        autoclose=True,
    ) as ws:
        _LOGGER.debug("ws events: connected")
        while not stop_event.is_set():
            try:
                msg = await ws.receive(timeout=_PING_TIMEOUT)
            except TimeoutError:
                continue
            if msg.type == WSMsgType.TEXT:
                _handle_event(msg.data, coordinator)
            elif msg.type == WSMsgType.CLOSED:
                _LOGGER.debug("ws events: server closed")
                return
            elif msg.type == WSMsgType.ERROR:
                _LOGGER.debug("ws events: socket error %s", ws.exception())
                return
        stop_task = asyncio.create_task(stop_event.wait())
        try:
            await asyncio.wait_for(stop_task, timeout=0.1)
        except TimeoutError:
            pass
        finally:
            stop_task.cancel()


def _handle_event(payload: str, coordinator: MnemosCoordinator) -> None:
    import json

    if not payload:
        return
    try:
        data: dict[str, Any] | None = json.loads(payload)
    except (TypeError, ValueError):
        return
    if not isinstance(data, dict):
        return
    event_type = data.get("type")
    if event_type in (EVENT_INBOX_NEW_FACE, EVENT_INBOX_BULK_CHANGED):
        _LOGGER.debug("ws events: %s -> refresh coordinator", event_type)
        coordinator.async_request_refresh()


async def safe_close(task: asyncio.Task | None) -> None:
    if task is None or task.done():
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError, ClientError, Exception):
        await task
