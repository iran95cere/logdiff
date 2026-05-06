"""Tests for logdiff.grouper module."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.grouper import GroupingError, group_by_field, group_summary


def make_change(field="level", before="info", after="error"):
    return FieldChange(field=field, before=before, after=after)


def make_diff(key, before_entry=None, after_entry=None, changes=None):
    return EntryDiff(
        key=key,
        before=before_entry,
        after=after_entry,
        changes=changes or [],
    )


# --- group_by_field ---

def test_group_by_field_groups_correctly():
    diffs = [
        make_diff("a", before_entry={"service": "auth", "msg": "ok"}),
        make_diff("b", before_entry={"service": "api", "msg": "fail"}),
        make_diff("c", before_entry={"service": "auth", "msg": "retry"}),
    ]
    groups = group_by_field(diffs, field="service")
    assert set(groups.keys()) == {"auth", "api"}
    assert len(groups["auth"]) == 2
    assert len(groups["api"]) == 1


def test_group_by_field_missing_field_uses_sentinel():
    diffs = [
        make_diff("a", before_entry={"service": "auth"}),
        make_diff("b", before_entry={"msg": "no service here"}),
    ]
    groups = group_by_field(diffs, field="service")
    assert "__missing__" in groups
    assert len(groups["__missing__"]) == 1


def test_group_by_field_none_before_uses_sentinel():
    diffs = [
        make_diff("added", before_entry=None, after_entry={"service": "new"}),
    ]
    groups = group_by_field(diffs, field="service", source="before")
    assert "__missing__" in groups


def test_group_by_field_source_after():
    diffs = [
        make_diff("a", after_entry={"env": "prod"}),
        make_diff("b", after_entry={"env": "staging"}),
        make_diff("c", after_entry={"env": "prod"}),
    ]
    groups = group_by_field(diffs, field="env", source="after")
    assert len(groups["prod"]) == 2
    assert len(groups["staging"]) == 1


def test_group_by_field_invalid_source_raises():
    with pytest.raises(GroupingError, match="source must be"):
        group_by_field([], field="service", source="unknown")


def test_group_by_field_empty_input():
    groups = group_by_field([], field="service")
    assert groups == {}


# --- group_summary ---

def test_group_summary_counts_total_and_changed():
    diffs = [
        make_diff("a", before_entry={"env": "prod"}, changes=[make_change()]),
        make_diff("b", before_entry={"env": "prod"}, changes=[]),
        make_diff("c", before_entry={"env": "staging"}, changes=[make_change()]),
    ]
    groups = group_by_field(diffs, field="env")
    summary = group_summary(groups)
    assert summary["prod"]["total"] == 2
    assert summary["prod"]["changed"] == 1
    assert summary["staging"]["total"] == 1
    assert summary["staging"]["changed"] == 1


def test_group_summary_empty_groups():
    assert group_summary({}) == {}
