"""Tests for the events.WebSocket task event dispatcher."""

from __future__ import annotations

import json

from mnemos.events import _handle_event


class _Coord:
    def __init__(self):
        self.refresh_calls = 0

    def async_request_refresh(self):
        self.refresh_calls += 1


def test_inbox_new_face_triggers_refresh():
    coord = _Coord()
    _handle_event(json.dumps({"type": "inbox.new_face", "crop_id": "x"}), coord)
    assert coord.refresh_calls == 1


def test_inbox_bulk_changed_triggers_refresh():
    coord = _Coord()
    _handle_event(json.dumps({"type": "inbox.bulk_changed", "count": 2}), coord)
    assert coord.refresh_calls == 1


def test_warmup_done_does_not_refresh():
    coord = _Coord()
    _handle_event(json.dumps({"type": "warmup.done", "model": "buffalo_s"}), coord)
    assert coord.refresh_calls == 0


def test_reindex_progress_does_not_refresh():
    coord = _Coord()
    _handle_event(
        json.dumps({"type": "reindex.progress", "model": "x", "done": 1, "total": 10}),
        coord,
    )
    assert coord.refresh_calls == 0


def test_garbage_payload_ignored():
    coord = _Coord()
    _handle_event("not json at all", coord)
    _handle_event("", coord)
    _handle_event("null", coord)
    _handle_event("[1,2,3]", coord)
    assert coord.refresh_calls == 0
