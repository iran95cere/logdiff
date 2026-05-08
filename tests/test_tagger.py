"""Tests for logdiff.tagger."""

import pytest
from logdiff.differ import EntryDiff, FieldChange
from logdiff.tagger import (
    TaggerError,
    TaggedDiff,
    tag_diffs,
    filter_by_tag,
    all_tags,
)


def make_change(field: str, before=None, after=None) -> FieldChange:
    return FieldChange(field=field, before=before, after=after)


def make_diff(
    key: str = "req-1",
    status: str = "modified",
    changes: list | None = None,
) -> EntryDiff:
    return EntryDiff(key=key, status=status, changes=changes or [])


# --- auto-tagging ---

def test_auto_tag_modified():
    diffs = [make_diff(status="modified")]
    result = tag_diffs(diffs)
    assert "modified" in result[0].tags


def test_auto_tag_added():
    diffs = [make_diff(status="added")]
    result = tag_diffs(diffs)
    assert "added" in result[0].tags
    assert "removed" not in result[0].tags


def test_auto_tag_removed():
    diffs = [make_diff(status="removed")]
    result = tag_diffs(diffs)
    assert "removed" in result[0].tags


def test_auto_tag_high_churn():
    changes = [make_change(f"field_{i}") for i in range(5)]
    diffs = [make_diff(changes=changes)]
    result = tag_diffs(diffs)
    assert "high-churn" in result[0].tags


def test_auto_tag_not_high_churn_below_threshold():
    changes = [make_change(f"field_{i}") for i in range(3)]
    diffs = [make_diff(changes=changes)]
    result = tag_diffs(diffs)
    assert "high-churn" not in result[0].tags


def test_auto_tag_status_change():
    changes = [make_change("status", before="ok", after="error")]
    diffs = [make_diff(changes=changes)]
    result = tag_diffs(diffs)
    assert "status-change" in result[0].tags


# --- extra_tags ---

def test_extra_tags_applied():
    diffs = [make_diff(key="req-42")]
    result = tag_diffs(diffs, extra_tags={"req-42": ["regression", "p1"]})
    assert "regression" in result[0].tags
    assert "p1" in result[0].tags


def test_extra_tags_no_duplicate_with_auto():
    diffs = [make_diff(key="req-1", status="modified")]
    result = tag_diffs(diffs, extra_tags={"req-1": ["modified"]})
    assert result[0].tags.count("modified") == 1


def test_extra_tags_unknown_key_ignored():
    diffs = [make_diff(key="req-1")]
    result = tag_diffs(diffs, extra_tags={"other-key": ["custom"]})
    assert "custom" not in result[0].tags


# --- auto=False ---

def test_auto_false_no_auto_tags():
    diffs = [make_diff(status="added")]
    result = tag_diffs(diffs, auto=False)
    assert result[0].tags == []


def test_auto_false_still_applies_extra_tags():
    diffs = [make_diff(key="req-1", status="added")]
    result = tag_diffs(diffs, extra_tags={"req-1": ["manual"]}, auto=False)
    assert result[0].tags == ["manual"]


# --- filter_by_tag ---

def test_filter_by_tag_returns_matching():
    diffs = [
        make_diff(key="a", status="added"),
        make_diff(key="b", status="removed"),
    ]
    tagged = tag_diffs(diffs)
    result = filter_by_tag(tagged, "added")
    assert len(result) == 1
    assert result[0].diff.key == "a"


def test_filter_by_tag_empty_tag_raises():
    with pytest.raises(TaggerError):
        filter_by_tag([], "")


# --- all_tags ---

def test_all_tags_returns_sorted_unique():
    diffs = [
        make_diff(key="a", status="added"),
        make_diff(key="b", status="removed"),
    ]
    tagged = tag_diffs(diffs)
    tags = all_tags(tagged)
    assert tags == sorted(set(tags))
    assert "added" in tags
    assert "removed" in tags


def test_all_tags_empty_list():
    assert all_tags([]) == []
