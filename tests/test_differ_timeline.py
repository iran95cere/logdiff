"""Tests for logdiff.differ_timeline."""

import pytest
from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_timeline import (
    TimelineError,
    TimelineSlice,
    Timeline,
    build_timeline,
)


def make_change(field: str = "status", before: str = "ok", after: str = "error") -> FieldChange:
    return FieldChange(field=field, before=before, after=after)


def make_diff(key: str = "req-1", changes: list | None = None) -> EntryDiff:
    return EntryDiff(key=key, changes=changes or [make_change()])


def make_empty_diff(key: str = "req-2") -> EntryDiff:
    return EntryDiff(key=key, changes=[])


# --- TimelineSlice ---

def test_slice_change_count_counts_only_changed():
    s = TimelineSlice(label="v1->v2", diffs=[make_diff(), make_empty_diff()])
    assert s.change_count == 1


def test_slice_entry_count():
    s = TimelineSlice(label="v1->v2", diffs=[make_diff(), make_diff("req-3")])
    assert s.entry_count == 2


def test_slice_change_count_no_diffs():
    s = TimelineSlice(label="v1->v2", diffs=[])
    assert s.change_count == 0


# --- Timeline ---

def test_timeline_labels():
    t = Timeline(slices=[
        TimelineSlice(label="a->b", diffs=[]),
        TimelineSlice(label="b->c", diffs=[]),
    ])
    assert t.labels == ["a->b", "b->c"]


def test_timeline_get_slice_found():
    s = TimelineSlice(label="a->b", diffs=[make_diff()])
    t = Timeline(slices=[s])
    assert t.get_slice("a->b") is s


def test_timeline_get_slice_missing_returns_none():
    t = Timeline(slices=[])
    assert t.get_slice("x->y") is None


def test_timeline_change_counts():
    t = Timeline(slices=[
        TimelineSlice(label="a->b", diffs=[make_diff(), make_empty_diff()]),
        TimelineSlice(label="b->c", diffs=[make_diff(), make_diff("req-3")]),
    ])
    counts = t.change_counts()
    assert counts == {"a->b": 1, "b->c": 2}


def test_timeline_peak_slice_returns_highest():
    t = Timeline(slices=[
        TimelineSlice(label="a->b", diffs=[make_diff()]),
        TimelineSlice(label="b->c", diffs=[make_diff(), make_diff("r2"), make_diff("r3")]),
    ])
    assert t.peak_slice().label == "b->c"


def test_timeline_peak_slice_empty_returns_none():
    t = Timeline(slices=[])
    assert t.peak_slice() is None


# --- build_timeline ---

def test_build_timeline_empty_raises():
    with pytest.raises(TimelineError, match="empty"):
        build_timeline({})


def test_build_timeline_creates_slices():
    tl = build_timeline({
        "v1->v2": [make_diff()],
        "v2->v3": [make_diff(), make_empty_diff()],
    })
    assert len(tl.slices) == 2
    assert tl.slices[0].label == "v1->v2"
    assert tl.slices[1].label == "v2->v3"


def test_build_timeline_preserves_order():
    labels = [f"v{i}->v{i+1}" for i in range(5)]
    data = {label: [] for label in labels}
    tl = build_timeline(data)
    assert tl.labels == labels
