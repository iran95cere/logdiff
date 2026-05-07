"""Tests for logdiff.snapshot module."""

import json
from pathlib import Path

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.reporter import DiffReport, build_report
from logdiff.snapshot import (
    SnapshotError,
    SnapshotComparison,
    compare_with_snapshot,
    load_snapshot,
    save_snapshot,
)


def make_change(field="status", before="ok", after="error"):
    return FieldChange(field=field, before=before, after=after)


def make_diff(key="req-1", changes=None, added=False, removed=False):
    return EntryDiff(
        key=key,
        changes=changes or [make_change()],
        added=added,
        removed=removed,
    )


def make_report(diffs):
    return build_report(diffs)


def test_save_snapshot_creates_file(tmp_path):
    report = make_report([make_diff()])
    out = str(tmp_path / "snap.json")
    save_snapshot(report, out)
    assert Path(out).exists()


def test_save_snapshot_content(tmp_path):
    report = make_report([make_diff()])
    out = str(tmp_path / "snap.json")
    save_snapshot(report, out)
    data = json.loads(Path(out).read_text())
    assert data["total_entries"] == report.total_entries
    assert data["changed_entries"] == report.changed_entries
    assert "change_rate" in data
    assert "most_changed_fields" in data


def test_save_snapshot_bad_path_raises():
    report = make_report([make_diff()])
    with pytest.raises(SnapshotError, match="Failed to write"):
        save_snapshot(report, "/nonexistent_dir/snap.json")


def test_load_snapshot_roundtrip(tmp_path):
    report = make_report([make_diff()])
    out = str(tmp_path / "snap.json")
    save_snapshot(report, out)
    data = load_snapshot(out)
    assert data["total_entries"] == report.total_entries


def test_load_snapshot_missing_raises():
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot("/no/such/file.json")


def test_load_snapshot_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json{")
    with pytest.raises(SnapshotError, match="Invalid JSON"):
        load_snapshot(str(bad))


def test_compare_with_snapshot_detects_regression(tmp_path):
    old_report = make_report([make_diff("a")])
    snap_path = str(tmp_path / "snap.json")
    save_snapshot(old_report, snap_path)

    new_diffs = [make_diff("a"), make_diff("b"), make_diff("c")]
    new_report = make_report(new_diffs)
    cmp = compare_with_snapshot(new_report, snap_path)
    assert cmp.regressed
    assert not cmp.improved


def test_compare_with_snapshot_detects_improvement(tmp_path):
    old_diffs = [make_diff("a"), make_diff("b")]
    old_report = make_report(old_diffs)
    snap_path = str(tmp_path / "snap.json")
    save_snapshot(old_report, snap_path)

    unchanged = EntryDiff(key="c", changes=[], added=False, removed=False)
    new_report = make_report([unchanged])
    cmp = compare_with_snapshot(new_report, snap_path)
    assert cmp.improved or cmp.change_rate_delta <= 0


def test_compare_new_and_removed_fields(tmp_path):
    old_report = make_report([make_diff(changes=[make_change("latency")])])
    snap_path = str(tmp_path / "snap.json")
    save_snapshot(old_report, snap_path)

    new_report = make_report([make_diff(changes=[make_change("status")])])
    cmp = compare_with_snapshot(new_report, snap_path)
    assert "status" in cmp.new_fields
    assert "latency" in cmp.removed_fields
