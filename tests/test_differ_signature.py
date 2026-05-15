"""Tests for logdiff.differ_signature."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_signature import (
    SignatureError,
    build_signature,
    signatures_match,
    _collect_field_signatures,
    _compute_fingerprint,
)


def make_change(field: str, change_type: str = "modified", before=None, after=None) -> FieldChange:
    return FieldChange(field=field, change_type=change_type, before=before, after=after)


def make_diff(key: str, *changes: FieldChange) -> EntryDiff:
    return EntryDiff(key=key, changes=list(changes))


# --- build_signature ---

def test_build_signature_empty_raises():
    with pytest.raises(SignatureError):
        build_signature([])


def test_build_signature_entry_count():
    diffs = [make_diff("a"), make_diff("b", make_change("status"))]
    sig = build_signature(diffs)
    assert sig.entry_count == 2


def test_build_signature_changed_count_excludes_unchanged():
    diffs = [make_diff("a"), make_diff("b", make_change("status"))]
    sig = build_signature(diffs)
    assert sig.changed_count == 1


def test_build_signature_field_signatures_populated():
    diffs = [
        make_diff("a", make_change("level", "modified"), make_change("msg", "added")),
        make_diff("b", make_change("level", "removed")),
    ]
    sig = build_signature(diffs)
    assert "level" in sig.field_signatures
    assert "msg" in sig.field_signatures


def test_build_signature_occurrence_count():
    diffs = [
        make_diff("a", make_change("level")),
        make_diff("b", make_change("level")),
    ]
    sig = build_signature(diffs)
    assert sig.field_signatures["level"].occurrence_count == 2


def test_build_signature_change_types_collected():
    diffs = [
        make_diff("a", make_change("level", "modified")),
        make_diff("b", make_change("level", "removed")),
    ]
    sig = build_signature(diffs)
    assert sig.field_signatures["level"].change_types == {"modified", "removed"}


def test_build_signature_fingerprint_is_deterministic():
    diffs = [make_diff("a", make_change("x", "modified"))]
    s1 = build_signature(diffs)
    s2 = build_signature(diffs)
    assert s1.fingerprint == s2.fingerprint


def test_build_signature_fingerprint_changes_with_different_fields():
    d1 = [make_diff("a", make_change("x", "modified"))]
    d2 = [make_diff("a", make_change("y", "modified"))]
    assert build_signature(d1).fingerprint != build_signature(d2).fingerprint


def test_active_fields_sorted():
    diffs = [
        make_diff("a", make_change("z"), make_change("a"), make_change("m")),
    ]
    sig = build_signature(diffs)
    assert sig.active_fields == ["a", "m", "z"]


# --- signatures_match ---

def test_signatures_match_identical_diffs():
    diffs = [make_diff("a", make_change("level"))]
    s1 = build_signature(diffs)
    s2 = build_signature(diffs)
    assert signatures_match(s1, s2) is True


def test_signatures_match_different_diffs():
    d1 = [make_diff("a", make_change("level"))]
    d2 = [make_diff("a", make_change("status"))]
    assert signatures_match(build_signature(d1), build_signature(d2)) is False


# --- repr ---

def test_diff_signature_repr_contains_fingerprint_prefix():
    diffs = [make_diff("a", make_change("f"))]
    sig = build_signature(diffs)
    r = repr(sig)
    assert sig.fingerprint[:8] in r


def test_field_signature_repr():
    from logdiff.differ_signature import FieldSignature
    fs = FieldSignature(field="level", change_types={"modified"}, occurrence_count=3)
    assert "level" in repr(fs)
    assert "3" in repr(fs)
