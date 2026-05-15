"""Tests for logdiff.differ_spotlight."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_spotlight import (
    SpotlightError,
    SpotlightEntry,
    SpotlightResult,
    build_spotlight,
    _score_change,
    _reason_for,
)


def make_change(
    before=None,
    after=None,
    change_type: str = "modified",
) -> FieldChange:
    return FieldChange(before=before, after=after, change_type=change_type)


def make_diff(key: str, **changes) -> EntryDiff:
    return EntryDiff(key=key, changes=changes)


# ---------------------------------------------------------------------------
# _score_change
# ---------------------------------------------------------------------------

def test_score_change_modified_base():
    change = make_change(before="a", after="b")
    assert _score_change("some_field", change) == pytest.approx(1.0)


def test_score_change_removed_adds_bonus():
    change = make_change(before="x", after=None, change_type="removed")
    assert _score_change("some_field", change) == pytest.approx(2.0)


def test_score_change_added_adds_half_bonus():
    change = make_change(before=None, after="x", change_type="added")
    assert _score_change("some_field", change) == pytest.approx(1.5)


def test_score_change_status_field_bonus():
    change = make_change(before="ok", after="error")
    assert _score_change("status", change) == pytest.approx(2.5)


def test_score_change_numeric_doubling_bonus():
    change = make_change(before=1, after=3)
    score = _score_change("latency", change)
    assert score == pytest.approx(1.5)


def test_score_change_numeric_not_doubled_no_bonus():
    change = make_change(before=10, after=11)
    score = _score_change("latency", change)
    assert score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# _reason_for
# ---------------------------------------------------------------------------

def test_reason_status_transition():
    change = make_change(before="ok", after="error")
    reason = _reason_for("status", change)
    assert "status transition" in reason
    assert "ok" in reason
    assert "error" in reason


def test_reason_removed_field():
    change = make_change(before="val", after=None, change_type="removed")
    reason = _reason_for("my_field", change)
    assert "removed" in reason
    assert "my_field" in reason


def test_reason_added_field():
    change = make_change(before=None, after="val", change_type="added")
    reason = _reason_for("new_field", change)
    assert "newly present" in reason


def test_reason_generic_modification():
    change = make_change(before="a", after="b")
    reason = _reason_for("host", change)
    assert "changed" in reason


# ---------------------------------------------------------------------------
# build_spotlight
# ---------------------------------------------------------------------------

def test_build_spotlight_empty_raises():
    with pytest.raises(SpotlightError):
        build_spotlight([])


def test_build_spotlight_returns_spotlight_result():
    diff = make_diff("req-1", status=make_change("ok", "error"))
    result = build_spotlight([diff])
    assert isinstance(result, SpotlightResult)


def test_build_spotlight_total_scanned():
    diffs = [make_diff(f"req-{i}", host=make_change("a", "b")) for i in range(5)]
    result = build_spotlight(diffs)
    assert result.total_scanned == 5


def test_build_spotlight_top_returns_highest_score():
    diff = make_diff(
        "req-1",
        status=make_change("ok", "error"),
        host=make_change("a", "b"),
    )
    result = build_spotlight([diff])
    assert result.top is not None
    assert result.top.field == "status"


def test_build_spotlight_respects_top_n():
    changes = {f"field_{i}": make_change(f"v{i}", f"w{i}") for i in range(20)}
    diff = make_diff("req-1", **changes)
    result = build_spotlight([diff], top_n=5)
    assert len(result.entries) <= 5


def test_build_spotlight_min_score_filters():
    diff = make_diff("req-1", host=make_change("a", "b"))  # score 1.0
    result = build_spotlight([diff], min_score=2.0)
    assert result.entries == []


def test_build_spotlight_entries_are_spotlight_entry_instances():
    diff = make_diff("req-1", status=make_change("ok", "fail"))
    result = build_spotlight([diff])
    for entry in result.entries:
        assert isinstance(entry, SpotlightEntry)


def test_build_spotlight_top_is_none_when_no_entries():
    diff = make_diff("req-1", host=make_change("a", "b"))
    result = build_spotlight([diff], min_score=99.0)
    assert result.top is None


def test_build_spotlight_entries_sorted_descending():
    diff = make_diff(
        "req-1",
        status=make_change("ok", "error"),
        host=make_change("x", None, change_type="removed"),
        path=make_change("p1", "p2"),
    )
    result = build_spotlight([diff])
    scores = [e.score for e in result.entries]
    assert scores == sorted(scores, reverse=True)
