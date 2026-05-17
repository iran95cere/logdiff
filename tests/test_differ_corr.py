"""Tests for logdiff.differ_corr."""
import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_corr import (
    CorrError,
    CorrResult,
    FieldPair,
    build_corr,
)


def make_change(f: str, before="a", after="b") -> FieldChange:
    return FieldChange(field=f, before=before, after=after)


def make_diff(key: str, fields) -> EntryDiff:
    return EntryDiff(key=key, changes=[make_change(f) for f in fields])


# ---------------------------------------------------------------------------
# FieldPair
# ---------------------------------------------------------------------------

def test_field_pair_correlation_zero_entries():
    fp = FieldPair(field_a="x", field_b="y", co_change_count=0, total_entries=0)
    assert fp.correlation == 0.0


def test_field_pair_correlation_computed():
    fp = FieldPair(field_a="x", field_b="y", co_change_count=3, total_entries=10)
    assert fp.correlation == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# build_corr – error cases
# ---------------------------------------------------------------------------

def test_build_corr_empty_raises():
    with pytest.raises(CorrError):
        build_corr([])


# ---------------------------------------------------------------------------
# build_corr – basic behaviour
# ---------------------------------------------------------------------------

def test_build_corr_returns_corr_result():
    diffs = [make_diff("e1", ["status", "latency"])]
    result = build_corr(diffs)
    assert isinstance(result, CorrResult)


def test_build_corr_entry_count():
    diffs = [make_diff("e1", ["a", "b"]), make_diff("e2", ["a"])]
    result = build_corr(diffs)
    assert result.entry_count == 2


def test_build_corr_detects_co_change():
    diffs = [
        make_diff("e1", ["status", "latency"]),
        make_diff("e2", ["status", "latency"]),
    ]
    result = build_corr(diffs)
    assert len(result.pairs) == 1
    pair = result.pairs[0]
    assert pair.field_a == "latency"
    assert pair.field_b == "status"
    assert pair.co_change_count == 2


def test_build_corr_no_pairs_when_single_field_per_entry():
    diffs = [make_diff("e1", ["only"]), make_diff("e2", ["only"])]
    result = build_corr(diffs)
    assert result.pairs == []


def test_build_corr_min_count_filters_rare_pairs():
    diffs = [
        make_diff("e1", ["a", "b"]),
        make_diff("e2", ["a", "c"]),
        make_diff("e3", ["a", "c"]),
    ]
    result = build_corr(diffs, min_count=2)
    # (a,c) appears twice; (a,b) appears once
    assert all(p.co_change_count >= 2 for p in result.pairs)


def test_build_corr_top_returns_sorted():
    diffs = [
        make_diff("e1", ["a", "b", "c"]),
        make_diff("e2", ["a", "b"]),
        make_diff("e3", ["a", "c"]),
    ]
    result = build_corr(diffs)
    top = result.top(2)
    assert len(top) == 2
    # highest correlation pair first
    assert top[0].correlation >= top[1].correlation


def test_build_corr_top_respects_n():
    diffs = [make_diff("e1", ["a", "b", "c", "d"])]
    result = build_corr(diffs)
    assert len(result.top(2)) == 2


def test_build_corr_unchanged_entry_does_not_add_pairs():
    diffs = [
        make_diff("e1", ["x", "y"]),
        EntryDiff(key="e2", changes=[]),  # no changes
    ]
    result = build_corr(diffs)
    assert result.entry_count == 2
    assert result.pairs[0].total_entries == 2
