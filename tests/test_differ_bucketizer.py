"""Tests for logdiff.differ_bucketizer."""
from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_bucketizer import (
    BucketizerError,
    BucketResult,
    Bucket,
    bucketize,
    _extract_numeric,
)


def make_change(field: str, after) -> FieldChange:
    return FieldChange(field=field, before=None, after=after, change_type="modified")


def make_diff(key: str, field: str, after) -> EntryDiff:
    return EntryDiff(key=key, changes=[make_change(field, after)])


# --- _extract_numeric ---

def test_extract_numeric_returns_float():
    diff = make_diff("a", "latency", "42.5")
    assert _extract_numeric(diff, "latency") == 42.5


def test_extract_numeric_returns_none_for_missing_field():
    diff = make_diff("a", "latency", "42")
    assert _extract_numeric(diff, "other") is None


def test_extract_numeric_returns_none_for_non_numeric():
    diff = make_diff("a", "latency", "high")
    assert _extract_numeric(diff, "latency") is None


def test_extract_numeric_returns_none_when_after_is_none():
    change = FieldChange(field="latency", before="5", after=None, change_type="removed")
    diff = EntryDiff(key="a", changes=[change])
    assert _extract_numeric(diff, "latency") is None


# --- bucketize ---

def test_bucketize_empty_raises():
    with pytest.raises(BucketizerError, match="empty"):
        bucketize([], "latency", [10, 100])


def test_bucketize_no_boundaries_raises():
    diff = make_diff("a", "latency", "5")
    with pytest.raises(BucketizerError, match="boundary"):
        bucketize([diff], "latency", [])


def test_bucketize_returns_bucket_result():
    diffs = [make_diff(str(i), "lat", str(i * 10)) for i in range(5)]
    result = bucketize(diffs, "lat", [20, 40])
    assert isinstance(result, BucketResult)
    assert result.target_field == "lat"


def test_bucketize_correct_bucket_count():
    diffs = [make_diff("x", "lat", "5")]
    result = bucketize(diffs, "lat", [10, 50])
    # 3 boundaries => 4 buckets: (-inf,10), [10,50), [50,+inf) — wait, 2 boundaries => 3 buckets
    assert len(result.buckets) == 3


def test_bucketize_places_entry_in_correct_bucket():
    diffs = [
        make_diff("low", "lat", "5"),
        make_diff("mid", "lat", "15"),
        make_diff("high", "lat", "55"),
    ]
    result = bucketize(diffs, "lat", [10, 50])
    assert result.buckets[0].count == 1   # (-inf, 10)
    assert result.buckets[1].count == 1   # [10, 50)
    assert result.buckets[2].count == 1   # [50, +inf)


def test_bucketize_skips_entries_without_target_field():
    diffs = [
        make_diff("a", "other", "5"),
        make_diff("b", "lat", "25"),
    ]
    result = bucketize(diffs, "lat", [10, 50])
    assert result.total_entries == 1


def test_bucketize_total_entries():
    diffs = [make_diff(str(i), "lat", str(i)) for i in range(10)]
    result = bucketize(diffs, "lat", [5])
    assert result.total_entries == 10


def test_bucket_get_returns_correct_bucket():
    diffs = [make_diff("a", "lat", "3")]
    result = bucketize(diffs, "lat", [10])
    bucket = result.get("[-inf, 10)")
    assert bucket is not None
    assert bucket.count == 1


def test_bucket_get_returns_none_for_missing_label():
    diffs = [make_diff("a", "lat", "3")]
    result = bucketize(diffs, "lat", [10])
    assert result.get("nonexistent") is None
