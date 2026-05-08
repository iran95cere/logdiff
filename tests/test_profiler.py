"""Tests for logdiff.profiler and logdiff.cli_profiler."""

from __future__ import annotations

import argparse
import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.profiler import profile_diffs, ProfilerError, DiffProfile
from logdiff.cli_profiler import add_profiler_args, handle_profiler


def make_change(field: str, before=None, after=None) -> FieldChange:
    return FieldChange(field=field, before=before, after=after)


def make_diff(key: str, *changes: FieldChange) -> EntryDiff:
    return EntryDiff(key=key, changes=list(changes))


# --- profiler core ---

def test_profile_empty_list():
    result = profile_diffs([])
    assert result.total_entries == 0
    assert result.total_changes == 0
    assert result.fields == {}
    assert result.most_volatile_field is None
    assert result.change_density == 0.0


def test_profile_counts_changes():
    diffs = [
        make_diff("req-1", make_change("status", "200", "500")),
        make_diff("req-2", make_change("status", "200", "404")),
    ]
    result = profile_diffs(diffs)
    assert result.total_entries == 2
    assert result.total_changes == 2
    assert "status" in result.fields
    assert result.fields["status"].change_count == 2
    assert result.fields["status"].modified_count == 2


def test_profile_detects_added_field():
    diffs = [make_diff("req-1", make_change("latency", None, 42))]
    result = profile_diffs(diffs)
    assert result.fields["latency"].added_count == 1
    assert result.fields["latency"].removed_count == 0
    assert result.fields["latency"].modified_count == 0


def test_profile_detects_removed_field():
    diffs = [make_diff("req-1", make_change("debug", "verbose", None))]
    result = profile_diffs(diffs)
    assert result.fields["debug"].removed_count == 1


def test_profile_unique_values():
    diffs = [
        make_diff("req-1", make_change("status", "200", "500")),
        make_diff("req-2", make_change("status", "200", "404")),
    ]
    result = profile_diffs(diffs)
    assert result.fields["status"].unique_before_values == 1  # only "200"
    assert result.fields["status"].unique_after_values == 2  # "500" and "404"


def test_profile_change_density():
    diffs = [
        make_diff("req-1", make_change("a", 1, 2), make_change("b", 3, 4)),
        make_diff("req-2"),
    ]
    result = profile_diffs(diffs)
    assert result.change_density == pytest.approx(1.0)


def test_profile_most_volatile_field():
    diffs = [
        make_diff("req-1", make_change("status", "200", "500")),
        make_diff("req-2", make_change("status", "200", "404")),
        make_diff("req-3", make_change("latency", 10, 20)),
    ]
    result = profile_diffs(diffs)
    assert result.most_volatile_field == "status"


def test_profile_raises_on_non_list():
    with pytest.raises(ProfilerError):
        profile_diffs("not a list")  # type: ignore


# --- CLI integration ---

def build_args(**kwargs) -> argparse.Namespace:
    defaults = {"top": 0, "min_changes": 1, "show_density": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_profiler_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_profiler_args(sub)
    parsed = parser.parse_args(["profile"])
    assert parsed is not None


def test_handle_profiler_prints_fields(capsys):
    diffs = [
        make_diff("req-1", make_change("status", "200", "500")),
        make_diff("req-2", make_change("status", "200", "404")),
    ]
    handle_profiler(build_args(), diffs)
    out = capsys.readouterr().out
    assert "status" in out


def test_handle_profiler_show_density(capsys):
    diffs = [make_diff("req-1", make_change("status", "200", "500"))]
    handle_profiler(build_args(show_density=True), diffs)
    out = capsys.readouterr().out
    assert "Change density" in out


def test_handle_profiler_top_limits_output(capsys):
    diffs = [
        make_diff("r1", make_change("a", 1, 2), make_change("b", 1, 2), make_change("c", 1, 2)),
    ]
    handle_profiler(build_args(top=1), diffs)
    out = capsys.readouterr().out
    lines = [l for l in out.strip().splitlines() if l and not l.startswith("-") and "Field" not in l and "Most" not in l]
    assert len(lines) == 1


def test_handle_profiler_min_changes_filters(capsys):
    diffs = [
        make_diff("r1", make_change("rare", 1, 2)),
        make_diff("r2", make_change("common", 1, 2)),
        make_diff("r3", make_change("common", 3, 4)),
    ]
    handle_profiler(build_args(min_changes=2), diffs)
    out = capsys.readouterr().out
    assert "common" in out
    assert "rare" not in out


def test_handle_profiler_no_matching_fields(capsys):
    diffs = [make_diff("r1", make_change("x", 1, 2))]
    handle_profiler(build_args(min_changes=99), diffs)
    out = capsys.readouterr().out
    assert "No fields match" in out
