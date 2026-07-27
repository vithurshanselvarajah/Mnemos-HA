"""Tests for the MnemosClient API wrapper.

These tests boot a real aiohttp `TestServer` and point a `MnemosClient` at it.
"""

from __future__ import annotations

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
from mnemos.api import MnemosClient
from mnemos.exceptions import MnemosApiError, MnemosAuthError, MnemosUnsupportedMedia


def _make_app(routes):
    app = web.Application()
    app.router.add_routes(routes)
    return app


async def test_base_url_no_ssl():
    c = MnemosClient(session=None, host="backend", port=8000, api_key="k")
    assert c.base_url == "http://backend:8000"


async def test_base_url_with_ssl():
    c = MnemosClient(
        session=None, host="backend", port=443, api_key="k", use_ssl=True
    )
    assert c.base_url == "https://backend:443"


async def test_ws_url_uses_ws_for_http():
    c = MnemosClient(session=None, host="backend", port=8000, api_key="k")
    assert c.ws_url == "ws://backend:8000/ws/events"


async def test_ws_url_uses_wss_for_https():
    c = MnemosClient(
        session=None, host="backend", port=443, api_key="k", use_ssl=True
    )
    assert c.ws_url == "wss://backend:443/ws/events"


async def test_api_key_setter():
    c = MnemosClient(session=None, host="h", port=1, api_key="old")
    c.api_key = "new"
    assert c.api_key == "new"


async def test_healthz_returns_payload():
    seen: dict = {}

    async def handler(request):
        seen["path"] = request.path
        return web.json_response({"status": "ok", "version": "1.2.3"})

    server = TestServer(_make_app([web.get("/healthz", handler)]))
    await server.start_server()
    try:
        async with ClientSession() as session:
            c = MnemosClient(session, host="localhost", port=server.port, api_key="k")
            out = await c.healthz()
        assert out == {"status": "ok", "version": "1.2.3"}
        assert seen["path"] == "/healthz"
    finally:
        await server.close()


async def test_unassigned_total_uses_count_only():
    seen_path: list[str] = []

    async def handler(request):
        seen_path.append(request.path_qs)
        return web.json_response(
            {"total": 7, "page": 1, "page_size": 0, "items": []}
        )

    server = TestServer(_make_app([web.get("/api/v1/faces/unassigned", handler)]))
    await server.start_server()
    try:
        async with ClientSession() as session:
            c = MnemosClient(session, host="localhost", port=server.port, api_key="k")
            out = await c.unassigned_total()
        assert out["total"] == 7
        assert "count_only=true" in seen_path[0]
    finally:
        await server.close()


async def test_identify_posts_multipart():
    seen: dict = {}

    async def handler(request):
        seen["content_type"] = request.headers.get("Content-Type", "")
        post = await request.post()
        seen["filename"] = post["file"].filename
        return web.json_response(
            {
                "recognized": [],
                "unknown_count": 0,
                "unknown_faces": [],
                "duplicates_skipped": 0,
            }
        )

    server = TestServer(_make_app([web.post("/api/v1/identify", handler)]))
    await server.start_server()
    try:
        async with ClientSession() as session:
            c = MnemosClient(session, host="localhost", port=server.port, api_key="k")
            out = await c.identify(b"\xff\xd8\xff\xe0", filename="a.jpg")
        assert out["unknown_count"] == 0
        assert seen["filename"] == "a.jpg"
        assert "multipart/form-data" in seen["content_type"]
    finally:
        await server.close()


async def test_401_raises_auth_error():
    async def handler(request):
        return web.json_response({"detail": "bad key"}, status=401)

    server = TestServer(_make_app([web.get("/healthz", handler)]))
    await server.start_server()
    try:
        async with ClientSession() as session:
            c = MnemosClient(session, host="localhost", port=server.port, api_key="k")
            with pytest.raises(MnemosAuthError):
                await c.healthz()
    finally:
        await server.close()


async def test_500_raises_api_error():
    async def handler(request):
        return web.json_response({"detail": "boom"}, status=500)

    server = TestServer(_make_app([web.get("/healthz", handler)]))
    await server.start_server()
    try:
        async with ClientSession() as session:
            c = MnemosClient(session, host="localhost", port=server.port, api_key="k")
            with pytest.raises(MnemosApiError) as exc:
                await c.healthz()
        assert exc.value.status == 500
    finally:
        await server.close()


async def test_unsupported_media_translated():
    async def handler(request):
        return web.json_response({"detail": "Unsupported image: bad"}, status=400)

    server = TestServer(_make_app([web.post("/api/v1/identify", handler)]))
    await server.start_server()
    try:
        async with ClientSession() as session:
            c = MnemosClient(session, host="localhost", port=server.port, api_key="k")
            with pytest.raises(MnemosUnsupportedMedia):
                await c.identify(b"\x00", filename="x.jpg")
    finally:
        await server.close()
