"""Tests for logdiff.differ_rank."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_rank import RankError, RankedDiff, rank_diffs


def make_change(
    field: str = "status",
    before: object = "ok",
    after: object = "error",
    change_type: str = "modified",
) -> FieldChange:
    return FieldChange(field=field, before=before, after=after, change_type=change_type)


def make_diff(
    key: str = "entry-1",
    changes: list[FieldChange] | None = None,
) -> EntryDiff:
    return EntryDiff(key=key, changes=changes or [])


# ---------------------------------------------------------------------------
# rank_diffs – basic behaviour
# ---------------------------------------------------------------------------

def test_rank_diffs_empty_raises() -> None:
    with pytest.raises(RankError):
        rank_diffs([])


def test_rank_diffs_returns_ranked_diff_instances() -> None:
    diffs = [make_diff("a", [make_change()])]
    result = rank_diffs(diffs)
    assert len(result) == 1
    assert isinstance(result[0], RankedDiff)


def test_rank_diffs_rank_starts_at_one() -> None:
    diffs = [make_diff("a", [make_change()])]
    result = rank_diffs(diffs)
    assert result[0].rank == 1


def test_rank_diffs_sorted_descending_by_score() -> None:
    low = make_diff("low", [make_change("cpu", 0.1, 0.2)])
    high = make_diff("high", [make_change("status", "ok", "error")])
    result = rank_diffs([low, high])
    assert result[0].score >= result[1].score


def test_rank_diffs_top_limits_results() -> None:
    diffs = [
        make_diff(f"entry-{i}", [make_change()])
        for i in range(5)
    ]
    result = rank_diffs(diffs, top=3)
    assert len(result) == 3


def test_rank_diffs_top_exceeding_length_returns_all() -> None:
    diffs = [make_diff("a", [make_change()])]
    result = rank_diffs(diffs, top=100)
    assert len(result) == 1


def test_rank_diffs_min_score_filters_low_entries() -> None:
    no_change = make_diff("empty")
    with_change = make_diff("changed", [make_change()])
    result = rank_diffs([no_change, with_change], min_score=0.5)
    keys = [rd.diff.key for rd in result]
    assert "empty" not in keys


def test_rank_diffs_min_score_zero_keeps_all() -> None:
    diffs = [
        make_diff("a", [make_change()]),
        make_diff("b"),
    ]
    result = rank_diffs(diffs, min_score=0.0)
    assert len(result) == 2


def test_rank_diffs_change_count_matches_diff() -> None:
    changes = [make_change("f1"), make_change("f2")]
    diffs = [make_diff("x", changes)]
    result = rank_diffs(diffs)
    assert result[0].change_count == 2


def test_rank_diffs_status_weight_increases_score() -> None:
    d = make_diff("s", [make_change("status", "ok", "error")])
    low_weight = rank_diffs([d], status_weight=1.0)[0].score
    high_weight = rank_diffs([d], status_weight=5.0)[0].score
    assert high_weight > low_weight


def test_rank_diffs_assigns_sequential_ranks() -> None:
    diffs = [
        make_diff(f"e{i}", [make_change()])
        for i in range(4)
    ]
    result = rank_diffs(diffs)
    ranks = [rd.rank for rd in result]
    assert ranks == list(range(1, len(result) + 1))
