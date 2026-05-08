"""Tests for logdiff.merger."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.merger import MergeResult, MergerError, merge_diffs, _merge_changes


def make_change(field: str, before=None, after=None, change_type: str = "modified") -> FieldChange:
    return FieldChange(field=field, before=before, after=after, change_type=change_type)


def make_diff(entry_id: str, changes=None, before=None, after=None) -> EntryDiff:
    b = before or {"id": entry_id, "status": "ok"}
    a = after or {"id": entry_id, "status": "ok"}
    return EntryDiff(before=b, after=a, changes=changes or [])


def test_merge_diffs_empty_sources_raises():
    with pytest.raises(MergerError):
        merge_diffs({})


def test_merge_diffs_single_source_returns_all():
    diffs = [make_diff("a"), make_diff("b")]
    result = merge_diffs({"src": diffs})
    assert result.total == 2
    assert result.conflict_count == 0


def test_merge_diffs_no_overlap_combines_all():
    src1 = [make_diff("a")]
    src2 = [make_diff("b")]
    result = merge_diffs({"s1": src1, "s2": src2})
    assert result.total == 2
    assert result.conflict_count == 0


def test_merge_diffs_overlap_detected_as_conflict():
    src1 = [make_diff("x")]
    src2 = [make_diff("x")]
    result = merge_diffs({"s1": src1, "s2": src2})
    assert "x" in result.conflicts
    assert result.conflicts["x"] == ["s1", "s2"]


def test_merge_diffs_prefer_last_overwrites_changes():
    c1 = make_change("status", before="ok", after="warn")
    c2 = make_change("status", before="ok", after="error")
    src1 = [make_diff("x", changes=[c1])]
    src2 = [make_diff("x", changes=[c2])]
    result = merge_diffs({"s1": src1, "s2": src2}, prefer_last=True)
    merged_entry = next(e for e in result.merged if (e.after or {}).get("id") == "x")
    status_change = next(c for c in merged_entry.changes if c.field == "status")
    assert status_change.after == "error"


def test_merge_diffs_prefer_first_keeps_original():
    c1 = make_change("status", before="ok", after="warn")
    c2 = make_change("status", before="ok", after="error")
    src1 = [make_diff("x", changes=[c1])]
    src2 = [make_diff("x", changes=[c2])]
    result = merge_diffs({"s1": src1, "s2": src2}, prefer_last=False)
    merged_entry = next(e for e in result.merged if (e.after or {}).get("id") == "x")
    status_change = next(c for c in merged_entry.changes if c.field == "status")
    assert status_change.after == "warn"


def test_merge_diffs_entries_without_id_appended_directly():
    no_id = EntryDiff(before={"val": 1}, after={"val": 2}, changes=[])
    result = merge_diffs({"src": [no_id]})
    assert result.total == 1


def test_source_counts_recorded():
    src1 = [make_diff("a"), make_diff("b")]
    src2 = [make_diff("c")]
    result = merge_diffs({"alpha": src1, "beta": src2})
    assert result.source_counts["alpha"] == 2
    assert result.source_counts["beta"] == 1


def test_merge_changes_prefers_incoming():
    base = [make_change("level", before=1, after=2)]
    incoming = [make_change("level", before=1, after=99)]
    merged = _merge_changes(base, incoming)
    assert len(merged) == 1
    assert merged[0].after == 99


def test_merge_changes_combines_distinct_fields():
    base = [make_change("a", before=1, after=2)]
    incoming = [make_change("b", before=3, after=4)]
    merged = _merge_changes(base, incoming)
    fields = {c.field for c in merged}
    assert fields == {"a", "b"}
