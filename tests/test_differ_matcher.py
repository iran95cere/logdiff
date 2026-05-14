"""Tests for logdiff.differ_matcher."""

import pytest

from logdiff.differ_matcher import (
    MatchedPair,
    MatchResult,
    MatcherError,
    _entry_similarity,
    match_entries,
)


def make_entry(**kwargs):
    return dict(kwargs)


# --- _entry_similarity ---

def test_entry_similarity_identical():
    a = {"id": "1", "status": "ok", "level": "info"}
    assert _entry_similarity(a, a) == 1.0


def test_entry_similarity_disjoint():
    a = {"x": 1}
    b = {"y": 2}
    assert _entry_similarity(a, b) == 0.0


def test_entry_similarity_partial():
    a = {"id": "1", "status": "ok"}
    b = {"id": "1", "status": "fail"}
    # 1 of 2 keys match
    assert _entry_similarity(a, b) == pytest.approx(0.5)


def test_entry_similarity_empty_both():
    assert _entry_similarity({}, {}) == 0.0


# --- match_entries by key ---

def test_match_entries_by_key_basic():
    before = [{"id": "a", "status": "ok"}]
    after = [{"id": "a", "status": "fail"}]
    result = match_entries(before, after, key_field="id")
    assert len(result.matched) == 1
    assert result.matched[0].key == "a"
    assert len(result.unmatched_before) == 0
    assert len(result.unmatched_after) == 0


def test_match_entries_unmatched_before():
    before = [{"id": "a"}, {"id": "b"}]
    after = [{"id": "a"}]
    result = match_entries(before, after, key_field="id")
    assert len(result.matched) == 1
    assert len(result.unmatched_before) == 1
    assert result.unmatched_before[0]["id"] == "b"


def test_match_entries_unmatched_after():
    before = [{"id": "a"}]
    after = [{"id": "a"}, {"id": "z"}]
    result = match_entries(before, after, key_field="id")
    assert len(result.matched) == 1
    assert len(result.unmatched_after) == 1
    assert result.unmatched_after[0]["id"] == "z"


def test_match_entries_missing_key_field_goes_unmatched():
    before = [{"name": "alice"}]
    after = [{"id": "1", "name": "alice"}]
    result = match_entries(before, after, key_field="id")
    assert len(result.matched) == 0
    assert len(result.unmatched_before) == 1


# --- match_rate ---

def test_match_rate_all_matched():
    before = [{"id": "1"}, {"id": "2"}]
    after = [{"id": "1"}, {"id": "2"}]
    result = match_entries(before, after)
    assert result.match_rate == pytest.approx(1.0)


def test_match_rate_none_matched():
    before = [{"id": "1"}]
    after = [{"id": "2"}]
    result = match_entries(before, after)
    assert result.match_rate == pytest.approx(0.0)


def test_match_rate_empty_inputs():
    result = match_entries([], [])
    assert result.match_rate == 0.0


# --- fuzzy matching ---

def test_fuzzy_match_finds_best_candidate():
    before = [{"status": "ok", "level": "info", "service": "api"}]
    after = [
        {"status": "ok", "level": "info", "service": "api"},
        {"status": "fail", "level": "error", "service": "db"},
    ]
    result = match_entries(before, after, key_field="id", fuzzy=True, threshold=0.5)
    assert len(result.matched) == 1
    assert result.matched[0].score >= 0.5


def test_fuzzy_no_match_below_threshold():
    before = [{"a": 1, "b": 2}]
    after = [{"c": 3, "d": 4}]
    result = match_entries(before, after, key_field="id", fuzzy=True, threshold=0.9)
    assert len(result.matched) == 0
    assert len(result.unmatched_before) == 1


# --- invalid threshold ---

def test_invalid_threshold_raises():
    with pytest.raises(MatcherError):
        match_entries([], [], threshold=1.5)


# --- MatchedPair repr ---

def test_matched_pair_repr():
    pair = MatchedPair(key="x", before={}, after={}, score=0.75)
    assert "x" in repr(pair)
    assert "0.75" in repr(pair)
