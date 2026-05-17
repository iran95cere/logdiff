"""Tests for logdiff.differ_velocity."""
from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_velocity import (
    FieldVelocity,
    VelocityError,
    VelocityReport,
    build_velocity,
)


def make_change(field: str, change_type: str = "modified") -> FieldChange:
    return FieldChange(field=field, before="a", after="b", change_type=change_type)


def make_diff(key: str, fields: list[str]) -> EntryDiff:
    return EntryDiff(key=key, changes=[make_change(f) for f in fields])


def test_build_velocity_empty_raises():
    with pytest.raises(VelocityError):
        build_velocity([])


def test_build_velocity_single_snapshot():
    diffs = [make_diff("e1", ["status", "level"]), make_diff("e2", ["status"])]
    report = build_velocity([("v1", diffs)])
    assert isinstance(report, VelocityReport)
    assert report.snapshots == ["v1"]
    assert len(report.field_velocities) == 2


def test_build_velocity_counts_per_snapshot():
    snap1 = [make_diff("e1", ["status"])]
    snap2 = [make_diff("e1", ["status", "level"]), make_diff("e2", ["status"])]
    report = build_velocity([("s1", snap1), ("s2", snap2)])
    status_fv = next(fv for fv in report.field_velocities if fv.field_name == "status")
    assert status_fv.counts[0] == 1  # s1
    assert status_fv.counts[1] == 2  # s2


def test_field_velocity_average():
    fv = FieldVelocity(field_name="f", counts=[2, 4, 6], snapshots=["a", "b", "c"])
    assert fv.average == pytest.approx(4.0)


def test_field_velocity_peak():
    fv = FieldVelocity(field_name="f", counts=[1, 9, 3], snapshots=["a", "b", "c"])
    assert fv.peak == 9


def test_field_velocity_is_accelerating_true():
    fv = FieldVelocity(field_name="f", counts=[1, 2, 5], snapshots=["a", "b", "c"])
    assert fv.is_accelerating is True


def test_field_velocity_is_accelerating_false():
    fv = FieldVelocity(field_name="f", counts=[5, 3, 1], snapshots=["a", "b", "c"])
    assert fv.is_accelerating is False


def test_field_velocity_is_accelerating_single():
    fv = FieldVelocity(field_name="f", counts=[3], snapshots=["a"])
    assert fv.is_accelerating is False


def test_field_velocity_repr():
    fv = FieldVelocity(field_name="cpu", counts=[2, 4], snapshots=["a", "b"])
    assert "cpu" in repr(fv)
    assert "avg=" in repr(fv)


def test_build_velocity_top_limits_results():
    diffs = [make_diff("e1", [f"field_{i}" for i in range(20)])]
    report = build_velocity([("s1", diffs)], top=5)
    assert len(report.field_velocities) <= 5


def test_velocity_report_top_field():
    snap1 = [make_diff("e1", ["status"])]
    snap2 = [make_diff("e1", ["status", "status"]), make_diff("e2", ["level"])]
    report = build_velocity([("s1", snap1), ("s2", snap2)])
    assert report.top_field is not None
    assert report.top_field.field_name == "status"


def test_velocity_report_top_field_empty():
    report = VelocityReport(snapshots=["s1"], field_velocities=[])
    assert report.top_field is None


def test_build_velocity_missing_field_in_snapshot_defaults_to_zero():
    snap1 = [make_diff("e1", ["alpha"])]
    snap2 = [make_diff("e1", ["beta"])]
    report = build_velocity([("s1", snap1), ("s2", snap2)])
    alpha = next(fv for fv in report.field_velocities if fv.field_name == "alpha")
    assert alpha.counts == [1, 0]
