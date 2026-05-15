"""Tests for logdiff.differ_trace."""
import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_trace import (
    TraceError,
    TracePoint,
    FieldTrace,
    TraceResult,
    build_trace,
)


def make_change(field, before, after, change_type="modified"):
    return FieldChange(field=field, before=before, after=after, change_type=change_type)


def make_diff(key, *changes):
    return EntryDiff(key=key, changes=list(changes))


def test_build_trace_empty_raises():
    with pytest.raises(TraceError):
        build_trace([])


def test_build_trace_single_snapshot():
    diffs = [make_diff("a", make_change("status", "ok", "error"))]
    result = build_trace([("v1", diffs)])
    assert "status" in result.traces
    assert len(result.traces["status"].points) == 1
    assert result.traces["status"].points[0].label == "v1"
    assert result.traces["status"].points[0].value == "error"


def test_build_trace_two_snapshots_same_field():
    diffs1 = [make_diff("a", make_change("level", "info", "warn"))]
    diffs2 = [make_diff("a", make_change("level", "warn", "error"))]
    result = build_trace([("v1", diffs1), ("v2", diffs2)])
    trace = result.traces["level"]
    assert len(trace.points) == 2
    assert trace.points[0].value == "warn"
    assert trace.points[1].value == "error"


def test_field_trace_total_changes_stable():
    trace = FieldTrace(field_name="x", points=[
        TracePoint("v1", "a"),
        TracePoint("v2", "a"),
        TracePoint("v3", "a"),
    ])
    assert trace.total_changes == 0
    assert trace.is_stable is True


def test_field_trace_total_changes_unstable():
    trace = FieldTrace(field_name="x", points=[
        TracePoint("v1", "a"),
        TracePoint("v2", "b"),
        TracePoint("v3", "a"),
    ])
    assert trace.total_changes == 2
    assert trace.is_stable is False


def test_trace_result_get_returns_trace():
    result = build_trace([("v1", [make_diff("e", make_change("f", None, 1))])])
    t = result.get("f")
    assert t is not None
    assert t.field_name == "f"


def test_trace_result_get_missing_returns_none():
    result = build_trace([("v1", [make_diff("e", make_change("f", None, 1))])])
    assert result.get("nonexistent") is None


def test_unstable_fields_returns_only_changed():
    diffs1 = [make_diff("a", make_change("x", 1, 2), make_change("y", "q", "q"))]
    diffs2 = [make_diff("a", make_change("x", 2, 2), make_change("y", "q", "q"))]
    result = build_trace([("v1", diffs1), ("v2", diffs2)])
    unstable = result.unstable_fields
    assert "x" in unstable


def test_build_trace_multiple_entries():
    diffs = [
        make_diff("a", make_change("code", 200, 404)),
        make_diff("b", make_change("code", 200, 500)),
    ]
    result = build_trace([("v1", diffs)])
    assert len(result.traces["code"].points) == 2


def test_build_trace_preserves_label_order():
    diffs1 = [make_diff("a", make_change("f", "a", "b"))]
    diffs2 = [make_diff("a", make_change("f", "b", "c"))]
    diffs3 = [make_diff("a", make_change("f", "c", "d"))]
    result = build_trace([("v1", diffs1), ("v2", diffs2), ("v3", diffs3)])
    labels = [p.label for p in result.traces["f"].points]
    assert labels == ["v1", "v2", "v3"]
