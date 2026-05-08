"""Tests for logdiff.watchlist and logdiff.cli_watchlist."""

import argparse
import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.watchlist import (
    Watchlist,
    WatchlistError,
    WatchlistMatch,
    match_watchlist,
    summarize_watchlist_matches,
)
from logdiff.cli_watchlist import add_watchlist_args, handle_watchlist


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_change(field, before=None, after=None, change_type="modified"):
    return FieldChange(field=field, before=before, after=after, change_type=change_type)


def make_diff(key, *fields):
    changes = [make_change(f) for f in fields]
    return EntryDiff(key=key, changes=changes, before={}, after={})


def build_args(**kwargs):
    ns = argparse.Namespace(watch=[], watch_summary=False)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


# ---------------------------------------------------------------------------
# Watchlist dataclass
# ---------------------------------------------------------------------------

def test_watchlist_add_and_contains():
    wl = Watchlist()
    wl.add("status")
    assert "status" in wl.fields


def test_watchlist_add_deduplicates():
    wl = Watchlist(fields=["status"])
    wl.add("status")
    assert wl.fields.count("status") == 1


def test_watchlist_add_invalid_raises():
    wl = Watchlist()
    with pytest.raises(WatchlistError):
        wl.add("")


def test_watchlist_remove_existing():
    wl = Watchlist(fields=["status", "level"])
    wl.remove("status")
    assert "status" not in wl.fields


def test_watchlist_remove_missing_raises():
    wl = Watchlist()
    with pytest.raises(WatchlistError):
        wl.remove("nonexistent")


def test_watchlist_is_empty():
    assert Watchlist().is_empty()
    assert not Watchlist(fields=["x"]).is_empty()


# ---------------------------------------------------------------------------
# match_watchlist
# ---------------------------------------------------------------------------

def test_match_watchlist_returns_hits():
    diffs = [make_diff("a", "status", "level"), make_diff("b", "message")]
    wl = Watchlist(fields=["status"])
    matches = match_watchlist(diffs, wl)
    assert len(matches) == 1
    assert matches[0].entry_diff.key == "a"
    assert "status" in matches[0].matched_fields


def test_match_watchlist_no_hits_returns_empty():
    diffs = [make_diff("a", "message")]
    wl = Watchlist(fields=["status"])
    assert match_watchlist(diffs, wl) == []


def test_match_watchlist_empty_watchlist_raises():
    diffs = [make_diff("a", "status")]
    with pytest.raises(WatchlistError):
        match_watchlist(diffs, Watchlist())


def test_match_watchlist_multiple_fields_hit():
    diffs = [make_diff("a", "status", "level", "env")]
    wl = Watchlist(fields=["status", "level"])
    matches = match_watchlist(diffs, wl)
    assert sorted(matches[0].matched_fields) == ["level", "status"]


# ---------------------------------------------------------------------------
# summarize_watchlist_matches
# ---------------------------------------------------------------------------

def test_summarize_counts_matches():
    matches = [
        WatchlistMatch(entry_diff=make_diff("a"), matched_fields=["status"]),
        WatchlistMatch(entry_diff=make_diff("b"), matched_fields=["status", "level"]),
    ]
    summary = summarize_watchlist_matches(matches)
    assert summary["total_matches"] == 2
    assert summary["field_hits"]["status"] == 2
    assert summary["field_hits"]["level"] == 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_add_watchlist_args_registers_flags():
    parser = argparse.ArgumentParser()
    add_watchlist_args(parser)
    args = parser.parse_args(["--watch", "status", "level", "--watch-summary"])
    assert args.watch == ["status", "level"]
    assert args.watch_summary is True


def test_handle_watchlist_no_flags_returns_all():
    diffs = [make_diff("a", "status"), make_diff("b", "level")]
    args = build_args(watch=[])
    result = handle_watchlist(args, diffs)
    assert result == diffs


def test_handle_watchlist_filters_correctly():
    diffs = [make_diff("a", "status"), make_diff("b", "level")]
    args = build_args(watch=["status"])
    result = handle_watchlist(args, diffs)
    assert len(result) == 1
    assert result[0].key == "a"


def test_handle_watchlist_summary_prints_and_returns_empty(capsys):
    diffs = [make_diff("a", "status"), make_diff("b", "status")]
    args = build_args(watch=["status"], watch_summary=True)
    result = handle_watchlist(args, diffs)
    assert result == []
    captured = capsys.readouterr()
    assert "2 match" in captured.out
    assert "status" in captured.out
