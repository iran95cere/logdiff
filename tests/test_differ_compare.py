"""Tests for logdiff.differ_compare."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_compare import CompareError, CompareResult, compare_diff_sets


def make_change(field="status", before="ok", after="error", change_type="modified"):
    return FieldChange(field=field, before=before, after=after, change_type=change_type)


def make_diff(key, changes=None):
    return EntryDiff(key=key, changes=changes or [])


# --- compare_diff_sets ---

def test_compare_diff_sets_only_in_a():
    a = [make_diff("key1", [make_change()])]
    b = [make_diff("key2", [make_change()])]
    result = compare_diff_sets(a, b)
    assert "key1" in result.only_in_a
    assert "key2" not in result.only_in_a


def test_compare_diff_sets_only_in_b():
    a = [make_diff("key1", [make_change()])]
    b = [make_diff("key2", [make_change()])]
    result = compare_diff_sets(a, b)
    assert "key2" in result.only_in_b


def test_compare_diff_sets_shared_keys():
    a = [make_diff("shared", [make_change()])]
    b = [make_diff("shared", [make_change()])]
    result = compare_diff_sets(a, b)
    assert "shared" in result.in_both
    assert result.only_in_a == []
    assert result.only_in_b == []


def test_compare_diff_sets_change_delta_positive():
    a = [make_diff("k", [make_change()])]
    b = [make_diff("k", [make_change(), make_change(field="level")])]
    result = compare_diff_sets(a, b)
    assert result.change_delta == 1


def test_compare_diff_sets_change_delta_negative():
    a = [make_diff("k", [make_change(), make_change(field="level")])]
    b = [make_diff("k", [make_change()])]
    result = compare_diff_sets(a, b)
    assert result.change_delta == -1


def test_compare_diff_sets_empty_inputs():
    result = compare_diff_sets([], [])
    assert result.only_in_a == []
    assert result.only_in_b == []
    assert result.in_both == []
    assert result.change_delta == 0


def test_compare_diff_sets_unchanged_entries_excluded():
    # entries with no changes should not appear in key sets
    a = [make_diff("no-change", [])]
    b = [make_diff("no-change", [])]
    result = compare_diff_sets(a, b)
    assert result.in_both == []


def test_compare_diff_sets_custom_labels():
    result = compare_diff_sets([], [], label_a="before", label_b="after")
    assert result.label_a == "before"
    assert result.label_b == "after"


def test_compare_diff_sets_invalid_input_raises():
    with pytest.raises(CompareError):
        compare_diff_sets(None, [])


def test_compare_result_repr():
    r = CompareResult(label_a="X", label_b="Y", only_in_a=["a"], only_in_b=[], in_both=["c"], change_delta=3)
    text = repr(r)
    assert "X" in text
    assert "Y" in text
