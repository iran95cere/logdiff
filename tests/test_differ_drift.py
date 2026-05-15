"""Tests for logdiff.differ_drift."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_drift import (
    DriftError,
    DriftReport,
    FieldDrift,
    _field_change_rates,
    detect_drift,
)


def make_change(field: str, change_type: str = "modified") -> FieldChange:
    return FieldChange(field=field, before="old", after="new", change_type=change_type)


def make_diff(key: str, *fields: str) -> EntryDiff:
    return EntryDiff(key=key, changes=[make_change(f) for f in fields])


# --- FieldDrift ---

def test_field_drift_delta_positive():
    fd = FieldDrift("status", rate_before=0.1, rate_after=0.4)
    assert abs(fd.delta - 0.3) < 1e-9
    assert fd.is_growing is True


def test_field_drift_delta_negative():
    fd = FieldDrift("status", rate_before=0.5, rate_after=0.2)
    assert fd.delta < 0
    assert fd.is_growing is False


# --- _field_change_rates ---

def test_field_change_rates_empty():
    assert _field_change_rates([]) == {}


def test_field_change_rates_single_entry():
    diffs = [make_diff("a", "status", "level")]
    rates = _field_change_rates(diffs)
    assert rates["status"] == pytest.approx(1.0)
    assert rates["level"] == pytest.approx(1.0)


def test_field_change_rates_partial():
    diffs = [
        make_diff("a", "status"),
        make_diff("b"),  # no changes
        make_diff("c", "status"),
    ]
    rates = _field_change_rates(diffs)
    assert rates["status"] == pytest.approx(2 / 3)


# --- detect_drift ---

def test_detect_drift_empty_before_raises():
    after = [make_diff("x", "f")]
    with pytest.raises(DriftError, match="before"):
        detect_drift([], after)


def test_detect_drift_empty_after_raises():
    before = [make_diff("x", "f")]
    with pytest.raises(DriftError, match="after"):
        detect_drift(before, [])


def test_detect_drift_returns_drift_report():
    before = [make_diff("a", "status"), make_diff("b")]
    after = [make_diff("c", "status"), make_diff("d", "status")]
    report = detect_drift(before, after)
    assert isinstance(report, DriftReport)


def test_detect_drift_field_rates():
    before = [make_diff("a", "level"), make_diff("b", "level")]
    after = [make_diff("c"), make_diff("d")]  # level disappears
    report = detect_drift(before, after)
    fd = next(f for f in report.drifted_fields if f.field_name == "level")
    assert fd.rate_before == pytest.approx(1.0)
    assert fd.rate_after == pytest.approx(0.0)


def test_detect_drift_new_field_in_after():
    before = [make_diff("a")]
    after = [make_diff("b", "new_field")]
    report = detect_drift(before, after)
    fd = next(f for f in report.drifted_fields if f.field_name == "new_field")
    assert fd.rate_before == pytest.approx(0.0)
    assert fd.rate_after == pytest.approx(1.0)


def test_detect_drift_sorted_by_abs_delta():
    before = [make_diff("a", "x"), make_diff("b", "x"), make_diff("c", "y")]
    after = [make_diff("d"), make_diff("e"), make_diff("f")]
    report = detect_drift(before, after)
    deltas = [abs(f.delta) for f in report.drifted_fields]
    assert deltas == sorted(deltas, reverse=True)


def test_drift_report_significant_filters_by_threshold():
    report = DriftReport(
        drifted_fields=[
            FieldDrift("a", 0.1, 0.2),  # delta 0.1 >= 0.05
            FieldDrift("b", 0.1, 0.12),  # delta 0.02 < 0.05
        ],
        threshold=0.05,
    )
    sig = report.significant
    assert len(sig) == 1
    assert sig[0].field_name == "a"


def test_drift_report_top_limits_results():
    fields = [FieldDrift(f"f{i}", 0.0, float(i) / 10) for i in range(10)]
    report = DriftReport(drifted_fields=fields)
    assert len(report.top(3)) == 3
