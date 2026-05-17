"""Tests for logdiff.differ_outlier."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_outlier import OutlierError, detect_outliers


def make_change(field: str = "status") -> FieldChange:
    return FieldChange(field=field, before="a", after="b", change_type="modified")


def make_diff(key: str, n_changes: int) -> EntryDiff:
    return EntryDiff(key=key, changes=[make_change(f"f{i}") for i in range(n_changes)])


def test_detect_outliers_empty_raises():
    with pytest.raises(OutlierError):
        detect_outliers([])


def test_detect_outliers_returns_report():
    diffs = [make_diff("a", 1), make_diff("b", 1), make_diff("c", 1)]
    report = detect_outliers(diffs)
    assert report.mean == 1.0
    assert report.has_outliers is False


def test_detect_outliers_finds_high_change_entry():
    # One entry with many changes should be flagged.
    diffs = [
        make_diff("normal-1", 1),
        make_diff("normal-2", 1),
        make_diff("normal-3", 1),
        make_diff("normal-4", 1),
        make_diff("spike", 20),
    ]
    report = detect_outliers(diffs, threshold=1.5)
    assert report.has_outliers
    assert report.outliers[0].entry_key == "spike"


def test_detect_outliers_z_score_positive_for_outlier():
    diffs = [
        make_diff("a", 1),
        make_diff("b", 1),
        make_diff("c", 1),
        make_diff("d", 50),
    ]
    report = detect_outliers(diffs, threshold=1.0)
    outlier = next(r for r in report.outliers if r.entry_key == "d")
    assert outlier.z_score > 1.0


def test_detect_outliers_sorted_by_z_score_descending():
    diffs = [
        make_diff("low", 1),
        make_diff("mid", 1),
        make_diff("high", 30),
        make_diff("highest", 50),
    ]
    report = detect_outliers(diffs, threshold=0.5)
    z_scores = [r.z_score for r in report.outliers]
    assert z_scores == sorted(z_scores, reverse=True)


def test_detect_outliers_std_dev_zero_no_outliers():
    # All entries identical — std dev is 0, z-scores are 0, nothing flagged.
    diffs = [make_diff(str(i), 3) for i in range(5)]
    report = detect_outliers(diffs, threshold=2.0)
    assert report.std_dev == 0.0
    assert not report.has_outliers


def test_detect_outliers_threshold_stored_in_report():
    diffs = [make_diff("x", 1), make_diff("y", 2)]
    report = detect_outliers(diffs, threshold=3.5)
    assert report.threshold == 3.5


def test_detect_outliers_mean_computed_correctly():
    diffs = [make_diff("a", 2), make_diff("b", 4), make_diff("c", 6)]
    report = detect_outliers(diffs, threshold=99.0)  # high threshold → no outliers
    assert abs(report.mean - 4.0) < 1e-9


def test_detect_outliers_result_carries_diff_reference():
    diffs = [
        make_diff("normal", 1),
        make_diff("normal2", 1),
        make_diff("normal3", 1),
        make_diff("big", 40),
    ]
    report = detect_outliers(diffs, threshold=1.0)
    assert any(r.diff.key == "big" for r in report.outliers)
