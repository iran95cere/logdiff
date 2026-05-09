"""Tests for logdiff.differ_heatmap."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_heatmap import (
    DiffHeatmap,
    FieldHeat,
    HeatmapError,
    build_heatmap,
)


def make_change(field, before, after):
    return FieldChange(field=field, before=before, after=after)


def make_diff(key, *changes):
    return EntryDiff(key=key, changes=list(changes))


# ---------------------------------------------------------------------------
# build_heatmap
# ---------------------------------------------------------------------------

def test_build_heatmap_empty_raises():
    with pytest.raises(HeatmapError):
        build_heatmap([])


def test_build_heatmap_counts_modified():
    diffs = [
        make_diff("a", make_change("status", "ok", "error")),
        make_diff("b", make_change("status", "ok", "warn")),
    ]
    hm = build_heatmap(diffs)
    assert hm.field_heats["status"].modified == 2
    assert hm.field_heats["status"].added == 0
    assert hm.field_heats["status"].removed == 0


def test_build_heatmap_counts_added():
    diffs = [make_diff("a", make_change("new_field", None, "value"))]
    hm = build_heatmap(diffs)
    assert hm.field_heats["new_field"].added == 1
    assert hm.field_heats["new_field"].modified == 0


def test_build_heatmap_counts_removed():
    diffs = [make_diff("a", make_change("old_field", "value", None))]
    hm = build_heatmap(diffs)
    assert hm.field_heats["old_field"].removed == 1


def test_build_heatmap_total_entries():
    diffs = [
        make_diff("a", make_change("x", 1, 2)),
        make_diff("b", make_change("y", 3, 4)),
        make_diff("c"),
    ]
    hm = build_heatmap(diffs)
    assert hm.total_entries == 3


def test_build_heatmap_multiple_fields():
    diffs = [
        make_diff(
            "a",
            make_change("status", "ok", "error"),
            make_change("latency", 10, 20),
        )
    ]
    hm = build_heatmap(diffs)
    assert "status" in hm.field_heats
    assert "latency" in hm.field_heats


# ---------------------------------------------------------------------------
# DiffHeatmap.hottest_fields
# ---------------------------------------------------------------------------

def test_hottest_fields_returns_top_n():
    diffs = [
        make_diff("a", make_change("f1", 1, 2), make_change("f2", 1, 2)),
        make_diff("b", make_change("f1", 3, 4)),
    ]
    hm = build_heatmap(diffs)
    top = hm.hottest_fields(top_n=1)
    assert len(top) == 1
    assert top[0].field_name == "f1"


def test_hottest_fields_descending_order():
    diffs = [
        make_diff("a", make_change("rare", 1, 2)),
        make_diff("b", make_change("common", 1, 2), make_change("common", 3, 4)),
        make_diff("c", make_change("common", 5, 6)),
    ]
    hm = build_heatmap(diffs)
    top = hm.hottest_fields(top_n=2)
    assert top[0].total >= top[1].total


# ---------------------------------------------------------------------------
# DiffHeatmap.coverage
# ---------------------------------------------------------------------------

def test_coverage_zero_entries():
    hm = DiffHeatmap(total_entries=0)
    assert hm.coverage() == 0.0


def test_coverage_with_changes():
    diffs = [
        make_diff("a", make_change("x", 1, 2)),
        make_diff("b"),
    ]
    hm = build_heatmap(diffs)
    # 1 unique changed field, 2 total entries -> 0.5
    assert hm.coverage() == 0.5


# ---------------------------------------------------------------------------
# FieldHeat.total
# ---------------------------------------------------------------------------

def test_field_heat_total():
    h = FieldHeat(field_name="f", modified=3, added=1, removed=2)
    assert h.total == 6
