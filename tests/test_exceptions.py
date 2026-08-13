"""Tests for typed exceptions raised by the API layer."""

from __future__ import annotations

import pytest
from mnemos.exceptions import (
    MnemosApiError,
    MnemosAuthError,
    MnemosConnectionError,
    MnemosError,
    MnemosUnsupportedMedia,
)


def test_hierarchy():
    assert issubclass(MnemosConnectionError, MnemosError)
    assert issubclass(MnemosAuthError, MnemosError)
    assert issubclass(MnemosApiError, MnemosError)
    assert issubclass(MnemosUnsupportedMedia, MnemosError)


def test_api_error_carries_status_and_detail():
    e = MnemosApiError(403, "forbidden")
    assert e.status == 403
    assert e.detail == "forbidden"
    assert "403" in str(e)
    assert "forbidden" in str(e)


def test_api_error_is_raisable():
    with pytest.raises(MnemosError):
        raise MnemosApiError(500, "boom")
