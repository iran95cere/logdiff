"""Tests for logdiff.differ_frequency."""
from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_frequency import (
    FrequencyError,
    FieldFrequency,
    FrequencyResult,
    build_frequency,
)


def make_change(field: str, kind: str = "modified") -> FieldChange:
    return FieldChange(field=field, before="a", after="b", change_type=kind)


def make_diff(key: str, *fields: str) -> EntryDiff:
    return EntryDiff(
        key=key,
        changes=[make_change(f) for f in fields],
    )


# ---------------------------------------------------------------------------
# FieldFrequency
# ---------------------------------------------------------------------------

def test_field_frequency_zero_entries():
    ff = FieldFrequency(field_name="status", change_count=0, entry_count=0)
    assert ff.frequency == 0.0


def test_field_frequency_computed():
    ff = FieldFrequency(field_name="status", change_count=3, entry_count=4)
    assert ff.frequency == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# FrequencyResult.top / .get
# ---------------------------------------------------------------------------

def test_frequency_result_top_returns_sorted():
    result = FrequencyResult(
        entry_count=10,
        field_frequencies=[
            FieldFrequency("a", 1, 10),
            FieldFrequency("b", 9, 10),
            FieldFrequency("c", 5, 10),
        ],
    )
    top = result.top(2)
    assert [ff.field_name for ff in top] == ["b", "c"]


def test_frequency_result_get_existing():
    result = FrequencyResult(
        entry_count=5,
        field_frequencies=[FieldFrequency("level", 3, 5)],
    )
    ff = result.get("level")
    assert ff is not None
    assert ff.change_count == 3


def test_frequency_result_get_missing_returns_none():
    result = FrequencyResult(entry_count=5, field_frequencies=[])
    assert result.get("nonexistent") is None


# ---------------------------------------------------------------------------
# build_frequency
# ---------------------------------------------------------------------------

def test_build_frequency_empty_raises():
    with pytest.raises(FrequencyError):
        build_frequency([])


def test_build_frequency_single_entry():
    diffs = [make_diff("e1", "status", "level")]
    result = build_frequency(diffs)
    assert result.entry_count == 1
    ff_status = result.get("status")
    assert ff_status is not None
    assert ff_status.change_count == 1
    assert ff_status.frequency == pytest.approx(1.0)


def test_build_frequency_counts_across_entries():
    diffs = [
        make_diff("e1", "status"),
        make_diff("e2", "status", "level"),
        make_diff("e3"),  # no changes
    ]
    result = build_frequency(diffs)
    assert result.entry_count == 3
    assert result.get("status").change_count == 2
    assert result.get("level").change_count == 1


def test_build_frequency_top_limits_results():
    diffs = [make_diff("e1", "a", "b", "c", "d")]
    result = build_frequency(diffs)
    assert len(result.top(2)) == 2


def test_build_frequency_field_not_present_returns_none():
    diffs = [make_diff("e1", "status")]
    result = build_frequency(diffs)
    assert result.get("missing_field") is None


def test_build_frequency_unchanged_entry_not_counted_in_field():
    diffs = [
        make_diff("e1", "status"),
        make_diff("e2"),  # no changes – should still count toward entry_count
    ]
    result = build_frequency(diffs)
    assert result.entry_count == 2
    assert result.get("status").frequency == pytest.approx(0.5)
