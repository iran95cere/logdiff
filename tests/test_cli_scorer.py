"""Tests for logdiff.cli_scorer."""

import argparse
import pytest
from logdiff.differ import EntryDiff, FieldChange
from logdiff.cli_scorer import add_scorer_args, handle_scorer


def make_change(field: str, change_type: str, before=None, after=None) -> FieldChange:
    return FieldChange(field=field, change_type=change_type, before=before, after=after)


def make_diff(key: str, changes) -> EntryDiff:
    return EntryDiff(key=key, before={}, after={}, changes=changes)


def build_args(**kwargs) -> argparse.Namespace:
    defaults = {"top_n": None, "min_score": None, "show_scores": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_scorer_args_registers_flags():
    parser = argparse.ArgumentParser()
    add_scorer_args(parser)
    args = parser.parse_args(["--top-n", "5", "--min-score", "2.0", "--show-scores"])
    assert args.top_n == 5
    assert args.min_score == pytest.approx(2.0)
    assert args.show_scores is True


def test_handle_scorer_no_flags_returns_all():
    diffs = [make_diff(f"r{i}", [make_change("f", "modified", i, i+1)]) for i in range(5)]
    args = build_args()
    result = handle_scorer(diffs, args)
    assert result == diffs


def test_handle_scorer_top_n_limits_results():
    diffs = [make_diff(f"r{i}", [make_change("f", "modified", i, i+1)]) for i in range(10)]
    args = build_args(top_n=3)
    result = handle_scorer(diffs, args)
    assert len(result) == 3


def test_handle_scorer_min_score_filters_low():
    low = make_diff("low", [make_change("msg", "modified", "a", "b")])   # score ~1.0
    high = make_diff("high", [
        make_change("status", "status_changed", "ok", "err"),  # score ~3.5
    ])
    args = build_args(min_score=2.0)
    result = handle_scorer([low, high], args)
    assert len(result) == 1
    assert result[0].key == "high"


def test_handle_scorer_top_n_and_min_score_combined():
    diffs = [
        make_diff("a", [make_change("status", "status_changed", "ok", "err")]),
        make_diff("b", [make_change("error", "added", None, "boom")]),
        make_diff("c", [make_change("msg", "modified", "x", "y")]),
    ]
    args = build_args(top_n=2, min_score=1.0)
    result = handle_scorer(diffs, args)
    assert len(result) <= 2


def test_handle_scorer_empty_diffs():
    args = build_args(top_n=5, min_score=1.0)
    result = handle_scorer([], args)
    assert result == []


def test_handle_scorer_min_score_excludes_all():
    diffs = [make_diff("x", [make_change("f", "modified", 1, 2)])]
    args = build_args(min_score=999.0)
    result = handle_scorer(diffs, args)
    assert result == []
