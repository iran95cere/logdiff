"""Tests for logdiff.differ_sampler."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_sampler import (
    SamplerError,
    SampleResult,
    deterministic_sample,
    sample_diffs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_change(field: str, before="a", after="b") -> FieldChange:
    return FieldChange(field=field, before=before, after=after, change_type="modified")


def make_diff(key: str, changed: bool = True) -> EntryDiff:
    changes = [make_change("status")] if changed else []
    return EntryDiff(key=key, changes=changes)


# ---------------------------------------------------------------------------
# sample_diffs
# ---------------------------------------------------------------------------

def test_sample_diffs_raises_without_n_or_fraction():
    with pytest.raises(SamplerError, match="neither"):
        sample_diffs([make_diff("a")], n=None, fraction=None)


def test_sample_diffs_raises_with_both_n_and_fraction():
    with pytest.raises(SamplerError, match="not both"):
        sample_diffs([make_diff("a")], n=1, fraction=0.5)


def test_sample_diffs_fraction_out_of_range():
    with pytest.raises(SamplerError, match="fraction"):
        sample_diffs([make_diff("a")], fraction=0.0)


def test_sample_diffs_negative_n_raises():
    with pytest.raises(SamplerError, match="non-negative"):
        sample_diffs([make_diff("a")], n=-1)


def test_sample_diffs_by_n_returns_correct_count():
    diffs = [make_diff(str(i)) for i in range(20)]
    result = sample_diffs(diffs, n=5, seed=42)
    assert result.sample_size == 5
    assert len(result.diffs) == 5


def test_sample_diffs_by_fraction_returns_correct_count():
    diffs = [make_diff(str(i)) for i in range(100)]
    result = sample_diffs(diffs, fraction=0.1, seed=0)
    assert result.sample_size == 10
    assert result.sample_rate == pytest.approx(0.1)


def test_sample_diffs_n_larger_than_pool_returns_all():
    diffs = [make_diff(str(i)) for i in range(5)]
    result = sample_diffs(diffs, n=100, seed=1)
    assert result.sample_size == 5
    assert result.total_input == 5


def test_sample_diffs_seed_is_reproducible():
    diffs = [make_diff(str(i)) for i in range(50)]
    r1 = sample_diffs(diffs, n=10, seed=7)
    r2 = sample_diffs(diffs, n=10, seed=7)
    assert [d.key for d in r1.diffs] == [d.key for d in r2.diffs]


def test_sample_diffs_different_seeds_differ():
    diffs = [make_diff(str(i)) for i in range(50)]
    r1 = sample_diffs(diffs, n=10, seed=1)
    r2 = sample_diffs(diffs, n=10, seed=999)
    # Very unlikely to be identical with 50 items and seed difference
    assert [d.key for d in r1.diffs] != [d.key for d in r2.diffs]


def test_sample_diffs_changed_only_filters_unchanged():
    diffs = [make_diff(str(i), changed=(i % 2 == 0)) for i in range(20)]
    result = sample_diffs(diffs, n=5, seed=0, changed_only=True)
    assert all(d.has_changes() for d in result.diffs)
    assert result.total_input == 10  # only 10 have changes


def test_sample_result_sample_rate_zero_on_empty():
    result = SampleResult(diffs=[], total_input=0, sample_size=0, seed=None)
    assert result.sample_rate == 0.0


# ---------------------------------------------------------------------------
# deterministic_sample
# ---------------------------------------------------------------------------

def test_deterministic_sample_fraction_out_of_range():
    with pytest.raises(SamplerError, match="fraction"):
        deterministic_sample([make_diff("x")], fraction=1.5)


def test_deterministic_sample_is_stable():
    diffs = [make_diff(str(i)) for i in range(200)]
    r1 = deterministic_sample(diffs, fraction=0.3)
    r2 = deterministic_sample(diffs, fraction=0.3)
    assert [d.key for d in r1.diffs] == [d.key for d in r2.diffs]


def test_deterministic_sample_seed_is_none():
    diffs = [make_diff(str(i)) for i in range(10)]
    result = deterministic_sample(diffs, fraction=0.5)
    assert result.seed is None


def test_deterministic_sample_total_input_matches_original():
    diffs = [make_diff(str(i)) for i in range(30)]
    result = deterministic_sample(diffs, fraction=0.25)
    assert result.total_input == 30
