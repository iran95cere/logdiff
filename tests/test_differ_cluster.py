"""Tests for logdiff.differ_cluster."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_cluster import (
    ClusterError,
    DiffCluster,
    _jaccard,
    cluster_diffs,
    cluster_summary,
)


def make_change(field: str, before="old", after="new", change_type="modified") -> FieldChange:
    return FieldChange(field=field, before=before, after=after, change_type=change_type)


def make_diff(key: str, *fields: str) -> EntryDiff:
    changes = [make_change(f) for f in fields]
    return EntryDiff(key=key, changes=changes)


# --- _jaccard ---

def test_jaccard_identical_sets():
    assert _jaccard({"a", "b"}, {"a", "b"}) == 1.0


def test_jaccard_disjoint_sets():
    assert _jaccard({"a"}, {"b"}) == 0.0


def test_jaccard_partial_overlap():
    result = _jaccard({"a", "b"}, {"b", "c"})
    assert abs(result - 1 / 3) < 1e-9


def test_jaccard_both_empty():
    assert _jaccard(set(), set()) == 1.0


# --- cluster_diffs ---

def test_cluster_diffs_empty_raises():
    with pytest.raises(ClusterError, match="empty"):
        cluster_diffs([])


def test_cluster_diffs_invalid_threshold_raises():
    diffs = [make_diff("k1", "field_a")]
    with pytest.raises(ClusterError, match="Threshold"):
        cluster_diffs(diffs, threshold=1.5)


def test_cluster_diffs_single_entry_forms_one_cluster():
    diffs = [make_diff("k1", "field_a", "field_b")]
    clusters = cluster_diffs(diffs)
    assert len(clusters) == 1
    assert clusters[0].size == 1


def test_cluster_diffs_identical_fields_grouped_together():
    diffs = [
        make_diff("k1", "field_a", "field_b"),
        make_diff("k2", "field_a", "field_b"),
    ]
    clusters = cluster_diffs(diffs, threshold=0.5)
    assert len(clusters) == 1
    assert clusters[0].size == 2


def test_cluster_diffs_disjoint_fields_form_separate_clusters():
    diffs = [
        make_diff("k1", "field_a"),
        make_diff("k2", "field_b"),
    ]
    clusters = cluster_diffs(diffs, threshold=0.5)
    assert len(clusters) == 2


def test_cluster_diffs_threshold_zero_groups_all():
    diffs = [
        make_diff("k1", "field_a"),
        make_diff("k2", "field_b"),
        make_diff("k3", "field_c"),
    ]
    clusters = cluster_diffs(diffs, threshold=0.0)
    assert len(clusters) == 1


def test_cluster_diffs_common_fields_is_intersection():
    diffs = [
        make_diff("k1", "field_a", "field_b"),
        make_diff("k2", "field_a", "field_c"),
    ]
    clusters = cluster_diffs(diffs, threshold=0.2)
    assert len(clusters) == 1
    assert "field_a" in clusters[0].common_fields


# --- cluster_summary ---

def test_cluster_summary_keys_and_structure():
    diffs = [
        make_diff("k1", "field_a", "field_b"),
        make_diff("k2", "field_a", "field_b"),
    ]
    clusters = cluster_diffs(diffs)
    summary = cluster_summary(clusters)
    assert 0 in summary
    assert summary[0]["size"] == 2
    assert isinstance(summary[0]["common_fields"], list)


def test_cluster_summary_fields_are_sorted():
    diffs = [
        make_diff("k1", "z_field", "a_field"),
        make_diff("k2", "z_field", "a_field"),
    ]
    clusters = cluster_diffs(diffs)
    summary = cluster_summary(clusters)
    fields = summary[0]["common_fields"]
    assert fields == sorted(fields)
