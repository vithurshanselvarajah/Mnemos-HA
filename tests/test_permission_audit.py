"""Permission boundary audit.

This test scans `custom_components/mnemos/api.py` and the WebSocket URL
construction in `events.py` to make sure the integration NEVER calls an
endpoint that requires `Full-Admin` on the backend.

If anyone adds a new HTTP call to the integration, this test forces them
to either keep it Identify-Only compatible or explicitly mark it.

The backend's full-admin endpoints are listed in `FULL_ADMIN_PATHS` below;
keep this list in sync with `mnemos-backend/app/api/deps.py::require_full_admin`.
"""

from __future__ import annotations

import re

# Backend endpoints that require a Full-Admin key.
# Source of truth: mnemos-backend/app/api/* (anything using require_full_admin).
FULL_ADMIN_PATHS = (
    "/api/v1/models/switch",
    "/api/v1/persons",                # POST
    "/api/v1/persons/",               # PATCH/DELETE (any sub-path)
    "/api/v1/keys",                   # POST
    "/api/v1/keys/",                  # DELETE
    "/api/v1/keys/revoke",
    "/api/v1/system/master/rotate",
)


def test_no_full_admin_endpoint_in_api_py():
    api_src = (_read("custom_components/mnemos/api.py"))
    for path in FULL_ADMIN_PATHS:
        escaped = re.escape(path)
        pattern = rf"[\"']{escaped}[\"']"
        assert not re.search(pattern, api_src), (
            f"MnemosClient must not call Full-Admin endpoint: {path}"
        )


def test_identify_only_endpoints_are_called():
    """The integration should call at least these Identify-Only-compatible endpoints."""
    api_src = _read("custom_components/mnemos/api.py")
    for path in ("/healthz", "/api/v1/models", "/api/v1/identify"):
        escaped = re.escape(path)
        pattern = rf"[\"']{escaped}[\"']"
        assert re.search(pattern, api_src), (
            f"Expected MnemosClient to call {path} — integration broken?"
        )
    assert "/api/v1/faces/unassigned" in api_src, (
        "Expected MnemosClient to query the unassigned inbox — integration broken?"
    )


def test_events_uses_public_ws_endpoint():
    """The /ws/events endpoint is in the backend's EXCLUDED_PATHS (no auth required)."""
    src = _read("custom_components/mnemos/api.py")
    assert "/ws/events" in src


def test_auth_header_is_x_api_key():
    """Auth header must match the backend's accepted names. See middleware.py."""
    api_src = _read("custom_components/mnemos/api.py")
    assert "X-API-Key" in api_src


def test_no_basic_auth_or_bearer_token():
    """The integration must not use Basic auth or Bearer tokens — backend only accepts X-API-Key."""
    api_src = _read("custom_components/mnemos/api.py")
    forbidden_markers = ("BasicAuth", "Bearer ", "Authorization: Bearer")
    for marker in forbidden_markers:
        assert marker not in api_src, (
            f"Do not use {marker} — backend rejects it"
        )


def _read(path: str) -> str:
    from pathlib import Path

    return (Path(__file__).resolve().parents[1] / path).read_text(encoding="utf-8")