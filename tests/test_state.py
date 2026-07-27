"""Tests for the typed state errors and entry helpers."""

from __future__ import annotations

import pytest
from mnemos.state import (
    MnemosEntryNotFound,
    MnemosEntryState,
    MnemosMultipleEntries,
    MnemosNotConfigured,
    get_entry_state,
    list_entry_states,
    resolve_entry_state,
)


def test_get_entry_state_raises_when_missing(hass):
    with pytest.raises(MnemosEntryNotFound):
        get_entry_state(hass, "nope")


def test_get_entry_state_returns_dataclass(hass):
    state = MnemosEntryState(client=None, coordinator=None)
    hass.data["mnemos"] = {"e1": state}
    assert get_entry_state(hass, "e1") is state


def test_list_entry_states_filters(hass):
    s1 = MnemosEntryState(client=None, coordinator=None)
    hass.data["mnemos"] = {"e1": s1, "garbage": "x"}
    assert list_entry_states(hass) == [s1]


def test_resolve_raises_when_empty(hass):
    with pytest.raises(MnemosNotConfigured):
        resolve_entry_state(hass)


def test_resolve_raises_when_multiple(hass):
    s1 = MnemosEntryState(
        client=type("C", (), {"base_url": "http://a:1"})(),
        coordinator=None,
    )
    s2 = MnemosEntryState(
        client=type("C", (), {"base_url": "http://b:1"})(),
        coordinator=None,
    )
    hass.data["mnemos"] = {"e1": s1, "e2": s2}
    with pytest.raises(MnemosMultipleEntries):
        resolve_entry_state(hass)


def test_resolve_picks_only_one(hass):
    s1 = MnemosEntryState(
        client=type("C", (), {"base_url": "http://a:1"})(),
        coordinator=None,
    )
    hass.data["mnemos"] = {"e1": s1}
    assert resolve_entry_state(hass) is s1


def test_set_last_identify_notifies_listeners():
    state = MnemosEntryState(client=None, coordinator=None)
    calls: list[int] = []
    state.last_identify_listeners.add(lambda: calls.append(1))
    state.set_last_identify({"persons": [], "unknown": True})
    assert state.last_identify == {"persons": [], "unknown": True}
    assert calls == [1]


def test_set_last_identify_continues_if_listener_raises():
    state = MnemosEntryState(client=None, coordinator=None)

    def _boom():
        raise RuntimeError("nope")

    state.last_identify_listeners.add(_boom)
    state.last_identify_listeners.add(lambda: None)
    state.set_last_identify({"x": 1})
    assert state.last_identify == {"x": 1}
