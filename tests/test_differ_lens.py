"""Tests for logdiff.differ_lens."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_lens import LensError, LensResult, apply_lens, _field_matches


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_change(field: str, before=None, after=None, kind="modified") -> FieldChange:
    return FieldChange(field=field, before=before, after=after, change_type=kind)


def make_diff(entry_id: str, *changes: FieldChange) -> EntryDiff:
    return EntryDiff(entry_id=entry_id, changes=list(changes))


# ---------------------------------------------------------------------------
# _field_matches
# ---------------------------------------------------------------------------

def test_field_matches_exact():
    assert _field_matches("status", ["status"]) is True


def test_field_matches_prefix():
    assert _field_matches("meta.region", ["meta"]) is True


def test_field_matches_no_match():
    assert _field_matches("latency", ["status", "meta"]) is False


def test_field_matches_partial_prefix_not_matched():
    # 'met' should NOT match 'meta.region'
    assert _field_matches("meta.region", ["met"]) is False


# ---------------------------------------------------------------------------
# apply_lens — basic
# ---------------------------------------------------------------------------

def test_apply_lens_empty_fields_raises():
    diff = make_diff("e1", make_change("status"))
    with pytest.raises(LensError):
        apply_lens([diff], fields=[])


def test_apply_lens_returns_only_matching_fields():
    diff = make_diff(
        "e1",
        make_change("status", "ok", "error"),
        make_change("latency", 100, 200),
    )
    results = apply_lens([diff], fields=["status"])
    assert len(results) == 1
    assert results[0].entry_id == "e1"
    assert len(results[0].focused_changes) == 1
    assert results[0].focused_changes[0].field == "status"


def test_apply_lens_omitted_count_is_correct():
    diff = make_diff(
        "e1",
        make_change("status"),
        make_change("latency"),
        make_change("region"),
    )
    results = apply_lens([diff], fields=["status"])
    assert results[0].omitted_count == 2


def test_apply_lens_excludes_entries_with_no_focused_changes():
    diff = make_diff("e1", make_change("latency", 10, 20))
    results = apply_lens([diff], fields=["status"])
    assert results == []


def test_apply_lens_prefix_matches_nested_fields():
    diff = make_diff(
        "e1",
        make_change("meta.region", "us-east", "eu-west"),
        make_change("meta.az", "a", "b"),
        make_change("status", "ok", "ok"),
    )
    results = apply_lens([diff], fields=["meta"])
    assert len(results) == 1
    assert len(results[0].focused_changes) == 2


# ---------------------------------------------------------------------------
# apply_lens — require_all
# ---------------------------------------------------------------------------

def test_apply_lens_require_all_passes_when_all_present():
    diff = make_diff(
        "e1",
        make_change("status", "ok", "error"),
        make_change("latency", 50, 200),
    )
    results = apply_lens([diff], fields=["status", "latency"], require_all=True)
    assert len(results) == 1


def test_apply_lens_require_all_drops_when_field_missing():
    diff = make_diff("e1", make_change("status", "ok", "error"))
    results = apply_lens([diff], fields=["status", "latency"], require_all=True)
    assert results == []


# ---------------------------------------------------------------------------
# LensResult helpers
# ---------------------------------------------------------------------------

def test_lens_result_has_changes_true():
    r = LensResult(entry_id="e1", focused_changes=[make_change("status")], omitted_count=0)
    assert r.has_changes() is True


def test_lens_result_has_changes_false():
    r = LensResult(entry_id="e1", focused_changes=[], omitted_count=3)
    assert r.has_changes() is False
