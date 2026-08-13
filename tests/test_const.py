"""Tests for the `mnemos.const` module — string literal sanity checks."""

from __future__ import annotations

from mnemos.const import (
    DATA_HEALTH,
    DATA_INBOX,
    DATA_LAST_IDENTIFY,
    DATA_MODEL,
    DOMAIN,
    EVENT_INBOX_BULK_CHANGED,
    EVENT_INBOX_NEW_FACE,
    EVENT_REINDEX_DONE,
    EVENT_REINDEX_PROGRESS,
    EVENT_WARMUP_DONE,
    EVENT_WARMUP_ERROR,
    MANUFACTURER,
    MODEL_NAME,
    STATE_NEVER_IDENTIFIED,
    STATE_NO_MATCH,
)


def test_domain_value():
    assert DOMAIN == "mnemos"


def test_state_placeholders_are_snake_case():
    assert STATE_NEVER_IDENTIFIED == "no_identify_yet"
    assert STATE_NO_MATCH == "no_match"
    assert "_" in STATE_NEVER_IDENTIFIED
    assert "_" in STATE_NO_MATCH


def test_event_constants_match_backend():
    assert EVENT_INBOX_NEW_FACE == "inbox.new_face"
    assert EVENT_INBOX_BULK_CHANGED == "inbox.bulk_changed"
    assert EVENT_WARMUP_DONE == "warmup.done"
    assert EVENT_WARMUP_ERROR == "warmup.error"
    assert EVENT_REINDEX_PROGRESS == "reindex.progress"
    assert EVENT_REINDEX_DONE == "reindex.done"


def test_data_keys():
    assert DATA_HEALTH == "health"
    assert DATA_MODEL == "model"
    assert DATA_INBOX == "inbox"
    assert DATA_LAST_IDENTIFY == "last_identify"


def test_manufacturer_and_model_non_empty():
    assert MANUFACTURER
    assert MODEL_NAME
    assert "Mnemos" in MODEL_NAME
