"""Pytest configuration for the Mnemos-HA integration.

Loads the real Home Assistant package and points pytest at the
`custom_components/mnemos` package. Provides a minimal `hass` fixture
backed by `homeassistant.core.HomeAssistant` (no test plugin needed).
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPONENTS_ROOT = REPO_ROOT / "custom_components"

if str(COMPONENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPONENTS_ROOT))


@pytest.fixture
async def hass(tmp_path):
    """Boot a real `homeassistant.core.HomeAssistant` for the test."""
    from homeassistant.core import HomeAssistant

    hass = HomeAssistant(str(tmp_path))
    hass.data = {}

    yield hass

    with contextlib.suppress(Exception):
        await hass.async_stop()
