"""Tests for logdiff.differ_trend."""

from __future__ import annotations

import pytest

from logdiff.differ import FieldChange, EntryDiff
from logdiff.differ_trend import (
    TrendError,
    TrendPoint,
    FieldTrend,
    DiffTrend,
    build_trend,
)


def make_change(field: str = "status", kind: str = "modified") -> FieldChange:
    return FieldChange(field=field, before="a", after="b", change_type=kind)


def make_diff(*fields: str) -> EntryDiff:
    changes = [make_change(f) for f in fields]
    return EntryDiff(key="entry-1", changes=changes)


# --- TrendPoint ---

def test_trend_point_repr():
    p = TrendPoint(label="v1", total_entries=10, changed_entries=4, change_rate=0.4)
    assert "v1" in repr(p)
    assert "0.40" in repr(p)


# --- FieldTrend ---

def test_field_trend_total():
    ft = FieldTrend(field="cpu", counts=[3, 5, 2])
    assert ft.total == 10


def test_field_trend_is_growing():
    ft = FieldTrend(field="cpu", counts=[1, 3])
    assert ft.is_growing is True
    assert ft.is_shrinking is False


def test_field_trend_is_shrinking():
    ft = FieldTrend(field="cpu", counts=[5, 2])
    assert ft.is_shrinking is True
    assert ft.is_growing is False


def test_field_trend_single_point_not_growing_or_shrinking():
    ft = FieldTrend(field="cpu", counts=[4])
    assert ft.is_growing is False
    assert ft.is_shrinking is False


# --- build_trend ---

def test_build_trend_empty_raises():
    with pytest.raises(TrendError):
        build_trend([])


def test_build_trend_single_snapshot():
    diffs = [make_diff("status"), make_diff()]
    trend = build_trend([{"label": "v1", "diffs": diffs}])
    assert len(trend.points) == 1
    assert trend.points[0].label == "v1"
    assert trend.points[0].total_entries == 2
    assert trend.points[0].changed_entries == 2


def test_build_trend_change_rate_zero_for_no_changes():
    diffs = [EntryDiff(key="e1", changes=[])]
    trend = build_trend([{"label": "v1", "diffs": diffs}])
    assert trend.points[0].change_rate == 0.0


def test_build_trend_field_counts_populated():
    diffs = [make_diff("cpu", "mem"), make_diff("cpu")]
    trend = build_trend([{"label": "v1", "diffs": diffs}])
    assert "cpu" in trend.field_trends
    assert trend.field_trends["cpu"].total == 2
    assert trend.field_trends["mem"].total == 1


def test_build_trend_multiple_snapshots_accumulate():
    s1 = {"label": "v1", "diffs": [make_diff("cpu")]}
    s2 = {"label": "v2", "diffs": [make_diff("cpu"), make_diff("cpu")]}
    trend = build_trend([s1, s2])
    assert len(trend.points) == 2
    assert trend.field_trends["cpu"].counts == [1, 2]
    assert trend.field_trends["cpu"].is_growing is True


def test_build_trend_avg_change_rate():
    s1 = {"label": "v1", "diffs": [make_diff("x")]}
    s2 = {"label": "v2", "diffs": [EntryDiff(key="e", changes=[])]}
    trend = build_trend([s1, s2])
    assert trend.avg_change_rate == pytest.approx(0.5)


def test_most_volatile_fields_top_n():
    diffs = [make_diff("a", "b", "c")]
    trend = build_trend([{"label": "v1", "diffs": diffs}])
    top = trend.most_volatile_fields(top=2)
    assert len(top) <= 2


def test_field_counts_padded_across_snapshots():
    s1 = {"label": "v1", "diffs": [make_diff("x")]}
    s2 = {"label": "v2", "diffs": [make_diff("y")]}
    trend = build_trend([s1, s2])
    assert len(trend.field_trends["x"].counts) == 2
    assert trend.field_trends["x"].counts[1] == 0
    assert len(trend.field_trends["y"].counts) == 2
    assert trend.field_trends["y"].counts[0] == 0
