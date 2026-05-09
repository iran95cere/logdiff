"""Tests for logdiff.differ_anomaly and logdiff.cli_anomaly."""

from __future__ import annotations

import argparse
import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_anomaly import (
    AnomalyError,
    AnomalyReport,
    FieldAnomaly,
    detect_anomalies,
    _field_change_counts,
    _mean,
    _std_dev,
)
from logdiff.cli_anomaly import add_anomaly_args, handle_anomaly


def make_change(field: str, kind: str = "modified") -> FieldChange:
    return FieldChange(field=field, before="a", after="b", kind=kind)


def make_diff(*fields: str, key: str = "id-1") -> EntryDiff:
    return EntryDiff(key=key, changes=[make_change(f) for f in fields])


# --- unit helpers ---

def test_mean_empty():
    assert _mean([]) == 0.0


def test_mean_values():
    assert _mean([2.0, 4.0, 6.0]) == pytest.approx(4.0)


def test_std_dev_single_value():
    assert _std_dev([5.0], mean=5.0) == 0.0


def test_std_dev_uniform():
    assert _std_dev([3.0, 3.0, 3.0], mean=3.0) == pytest.approx(0.0)


def test_field_change_counts_aggregates():
    diffs = [
        make_diff("status", "latency"),
        make_diff("status"),
    ]
    counts = _field_change_counts(diffs)
    assert counts["status"] == 2
    assert counts["latency"] == 1


def test_field_change_counts_empty_diffs():
    assert _field_change_counts([]) == {}


# --- detect_anomalies ---

def test_detect_anomalies_empty_raises():
    with pytest.raises(AnomalyError):
        detect_anomalies([])


def test_detect_anomalies_no_changes_returns_empty_report():
    diffs = [EntryDiff(key="k1", changes=[])]
    report = detect_anomalies(diffs)
    assert not report.has_anomalies
    assert report.top_anomaly is None


def test_detect_anomalies_flags_high_z_field():
    # 'status' changes 10x, others change 1x each — should be flagged
    diffs = [make_diff("status") for _ in range(10)]
    diffs += [make_diff("latency"), make_diff("code"), make_diff("host")]
    report = detect_anomalies(diffs, threshold=1.5)
    field_names = [a.field_name for a in report.anomalies]
    assert "status" in field_names


def test_detect_anomalies_uniform_no_flags():
    # All fields change the same number of times → std_dev=0, z=0
    diffs = [make_diff("a"), make_diff("b"), make_diff("c")]
    report = detect_anomalies(diffs, threshold=2.0)
    assert not report.has_anomalies


def test_detect_anomalies_sorted_by_z_descending():
    diffs = [make_diff("hot") for _ in range(20)]
    diffs += [make_diff("warm") for _ in range(5)]
    diffs += [make_diff("cold")]
    report = detect_anomalies(diffs, threshold=0.5)
    z_scores = [a.z_score for a in report.anomalies]
    assert z_scores == sorted(z_scores, reverse=True)


def test_detect_anomalies_threshold_respected():
    diffs = [make_diff("status") for _ in range(10)]
    diffs += [make_diff("other")]
    # Very high threshold — nothing flagged
    report = detect_anomalies(diffs, threshold=100.0)
    assert not report.has_anomalies


# --- cli ---

def build_args(**kwargs) -> argparse.Namespace:
    defaults = {"threshold": 2.0, "top": 5, "quiet": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_anomaly_args_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_anomaly_args(sub)
    parsed = root.parse_args(["anomaly"])
    assert parsed is not None


def test_handle_anomaly_no_anomalies_prints_message():
    diffs = [make_diff("a"), make_diff("b")]
    out = []
    code = handle_anomaly(build_args(), diffs, print_fn=out.append)
    assert code == 0
    assert any("No anomalies" in line for line in out)


def test_handle_anomaly_quiet_prints_field_names_only():
    diffs = [make_diff("status") for _ in range(15)]
    diffs += [make_diff("other")]
    out = []
    code = handle_anomaly(
        build_args(threshold=1.0, quiet=True), diffs, print_fn=out.append
    )
    assert code == 0
    assert "status" in out
    # No z= formatting in quiet mode
    assert not any("z=" in line for line in out)


def test_handle_anomaly_top_limits_output():
    # Create 6 distinct anomalous fields
    diffs = []
    for i in range(6):
        diffs += [make_diff(f"field_{i}") for _ in range(10 + i)]
    diffs += [make_diff("rare")]
    out = []
    handle_anomaly(build_args(threshold=0.5, top=3), diffs, print_fn=out.append)
    # Header + 3 anomaly lines
    anomaly_lines = [l for l in out if "count=" in l]
    assert len(anomaly_lines) <= 3


def test_handle_anomaly_empty_diffs_returns_error():
    out = []
    code = handle_anomaly(build_args(), [], print_fn=out.append)
    assert code == 1
    assert any("error" in line for line in out)
