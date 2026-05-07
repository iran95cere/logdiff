"""Tests for logdiff.annotator."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.annotator import (
    AnnotatedChange,
    AnnotatedDiff,
    annotate_diff,
    annotate_diffs,
    _annotate_change,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_change(field, before, after):
    return FieldChange(field=field, before=before, after=after)


def make_diff(entry_id, *changes):
    return EntryDiff(entry_id=entry_id, changes=list(changes))


# ---------------------------------------------------------------------------
# _annotate_change
# ---------------------------------------------------------------------------

def test_annotate_change_status_transition():
    fc = make_change("status", "ok", "error")
    ac = _annotate_change(fc)
    assert ac.note == "Status transition detected"


def test_annotate_change_new_field():
    fc = make_change("latency", None, 42)
    ac = _annotate_change(fc)
    assert ac.note == "New field introduced"


def test_annotate_change_removed_field():
    fc = make_change("latency", 42, None)
    ac = _annotate_change(fc)
    assert ac.note == "Field removed"


def test_annotate_change_numeric_increase():
    fc = make_change("response_time", 100, 250)
    ac = _annotate_change(fc)
    assert ac.note == "Numeric value increased"


def test_annotate_change_numeric_decrease():
    fc = make_change("response_time", 250, 100)
    ac = _annotate_change(fc)
    assert ac.note == "Numeric value decreased"


def test_annotate_change_no_matching_rule():
    fc = make_change("message", "hello", "world")
    ac = _annotate_change(fc)
    assert ac.note is None


def test_annotate_change_custom_rule_takes_priority():
    fc = make_change("status", "ok", "error")
    ac = _annotate_change(fc, custom_rules={"status": "Custom status note"})
    assert ac.note == "Custom status note"


def test_annotate_change_custom_rule_other_field_unaffected():
    fc = make_change("level", "info", "warn")
    ac = _annotate_change(fc, custom_rules={"status": "Custom status note"})
    assert ac.note is None


# ---------------------------------------------------------------------------
# annotate_diff
# ---------------------------------------------------------------------------

def test_annotate_diff_returns_annotated_diff():
    diff = make_diff("req-1", make_change("status", "ok", "error"))
    ad = annotate_diff(diff)
    assert isinstance(ad, AnnotatedDiff)
    assert ad.entry_id == "req-1"
    assert len(ad.annotated_changes) == 1


def test_annotate_diff_has_notes_true():
    diff = make_diff("req-1", make_change("status", "ok", "error"))
    ad = annotate_diff(diff)
    assert ad.has_notes() is True


def test_annotate_diff_has_notes_false():
    diff = make_diff("req-1", make_change("message", "hello", "world"))
    ad = annotate_diff(diff)
    assert ad.has_notes() is False


def test_annotate_diff_empty_changes():
    diff = make_diff("req-1")
    ad = annotate_diff(diff)
    assert ad.annotated_changes == []
    assert ad.has_notes() is False


# ---------------------------------------------------------------------------
# annotate_diffs
# ---------------------------------------------------------------------------

def test_annotate_diffs_returns_list():
    diffs = [
        make_diff("a", make_change("status", "ok", "fail")),
        make_diff("b", make_change("count", 1, 5)),
    ]
    result = annotate_diffs(diffs)
    assert len(result) == 2
    assert all(isinstance(r, AnnotatedDiff) for r in result)


def test_annotate_diffs_empty_list():
    assert annotate_diffs([]) == []


def test_annotate_diffs_passes_custom_rules():
    diffs = [make_diff("x", make_change("env", "staging", "prod"))]
    result = annotate_diffs(diffs, custom_rules={"env": "Environment promoted"})
    assert result[0].annotated_changes[0].note == "Environment promoted"
