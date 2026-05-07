"""Tests for logdiff.scorer."""

import pytest
from logdiff.differ import EntryDiff, FieldChange
from logdiff.scorer import (
    ScoredDiff,
    score_diff,
    score_diffs,
    top_n,
    _score_change,
)


def make_change(field: str, change_type: str, before=None, after=None) -> FieldChange:
    return FieldChange(field=field, change_type=change_type, before=before, after=after)


def make_diff(key: str, changes) -> EntryDiff:
    return EntryDiff(key=key, before={}, after={}, changes=changes)


def test_score_change_modified():
    c = make_change("message", "modified", "a", "b")
    assert _score_change(c) == pytest.approx(1.0)


def test_score_change_removed():
    c = make_change("message", "removed", "a", None)
    assert _score_change(c) == pytest.approx(1.2)


def test_score_change_status_field_bonus():
    c = make_change("status", "modified", "ok", "error")
    # base 1.0 + bonus 1.5
    assert _score_change(c) == pytest.approx(2.5)


def test_score_change_status_changed_type():
    c = make_change("level", "status_changed", "info", "error")
    # base 2.0 + bonus 1.2
    assert _score_change(c) == pytest.approx(3.2)


def test_score_diff_sums_changes():
    diff = make_diff("req-1", [
        make_change("message", "modified", "a", "b"),
        make_change("code", "removed", 200, None),
    ])
    result = score_diff(diff)
    assert isinstance(result, ScoredDiff)
    # message: 1.0, code: 1.2 + 1.1 = 2.3 => total 3.3
    assert result.score == pytest.approx(3.3)
    assert "message" in result.breakdown
    assert "code" in result.breakdown


def test_score_diff_no_changes():
    diff = make_diff("req-empty", [])
    result = score_diff(diff)
    assert result.score == 0.0
    assert result.breakdown == {}


def test_score_diffs_sorted_descending():
    d1 = make_diff("low", [make_change("message", "modified", "a", "b")])
    d2 = make_diff("high", [
        make_change("status", "status_changed", "ok", "fail"),
        make_change("error", "added", None, "timeout"),
    ])
    d3 = make_diff("mid", [make_change("code", "removed", 200, None)])
    results = score_diffs([d1, d2, d3])
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0].entry_diff.key == "high"


def test_score_diffs_empty_list():
    assert score_diffs([]) == []


def test_top_n_returns_correct_count():
    diffs = [
        make_diff(f"req-{i}", [make_change("field", "modified", i, i + 1)])
        for i in range(10)
    ]
    scored = score_diffs(diffs)
    top = top_n(scored, 3)
    assert len(top) == 3


def test_top_n_raises_on_zero():
    with pytest.raises(ValueError):
        top_n([], 0)


def test_scored_diff_repr():
    diff = make_diff("req-x", [])
    sd = ScoredDiff(entry_diff=diff, score=4.2)
    assert "req-x" in repr(sd)
    assert "4.20" in repr(sd)
