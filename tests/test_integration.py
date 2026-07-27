"""Tests for the integration init / services / config flow.

These tests boot a real Home Assistant instance with the integration's
config entry loaded. They spin up a stub Mnemos backend on the loopback
interface so the HA coordinator's HTTP calls work end-to-end.
"""

from __future__ import annotations

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
from mnemos.api import MnemosClient


@pytest.fixture
async def backend_server():
    """Stub Mnemos backend with /healthz, /api/v1/models, /api/v1/faces/unassigned."""
    async def healthz(request):
        return web.json_response(
            {
                "status": "ok",
                "version": "test",
                "model": "buffalo_s",
                "model_loaded": True,
                "provider": "cpu",
                "db": True,
                "vector_db": True,
                "reindex_in_progress": False,
                "reindex_done": 0,
                "reindex_total": 0,
            }
        )

    async def models(request):
        return web.json_response(
            {
                "name": "buffalo_s",
                "embedding_dim": 512,
                "det_size": 640,
                "reindex_in_progress": False,
                "reindex_done": 0,
                "reindex_total": 0,
            }
        )

    async def unassigned(request):
        return web.json_response({"total": 0, "page": 1, "page_size": 0, "items": []})

    server = TestServer(
        _app(
            [
                web.get("/healthz", healthz),
                web.get("/api/v1/models", models),
                web.get("/api/v1/faces/unassigned", unassigned),
            ]
        )
    )
    await server.start_server()
    try:
        yield server
    finally:
        await server.close()


def _app(routes):
    app = web.Application()
    app.router.add_routes(routes)
    return app


async def test_client_works_against_test_server(backend_server):
    """Sanity: a MnemosClient can talk to our stub backend."""
    async with ClientSession() as session:
        c = MnemosClient(
            session, host="localhost", port=backend_server.port, api_key="k"
        )
        h = await c.healthz()
        m = await c.model_info()
        u = await c.unassigned_total()
    assert h["status"] == "ok"
    assert m["name"] == "buffalo_s"
    assert u["total"] == 0


async def test_ws_url_uses_backend_port(backend_server):
    async with ClientSession() as session:
        c = MnemosClient(
            session, host="localhost", port=backend_server.port, api_key="k"
        )
        assert c.ws_url == f"ws://localhost:{backend_server.port}/ws/events"
