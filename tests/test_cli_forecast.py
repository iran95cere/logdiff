"""Tests for logdiff.cli_forecast."""

from __future__ import annotations

import argparse
import json
import os
import pytest

from logdiff.cli_forecast import (
    add_forecast_args,
    handle_forecast,
    _build_histories_from_diffs,
)
from logdiff.differ import EntryDiff, FieldChange


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_change(field: str, change_type: str = "modified") -> FieldChange:
    return FieldChange(field=field, before="a", after="b", change_type=change_type)


def make_diff(key: str, *fields: str) -> EntryDiff:
    return EntryDiff(key=key, changes=[make_change(f) for f in fields])


def build_args(**kwargs) -> argparse.Namespace:
    defaults = {"steps": 3, "top": 5, "min_history": 2, "snapshots": []}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# add_forecast_args
# ---------------------------------------------------------------------------

def test_add_forecast_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_forecast_args(sub)
    args = parser.parse_args(["forecast", "a.json", "b.json"])
    assert args.snapshots == ["a.json", "b.json"]


def test_add_forecast_args_default_steps():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_forecast_args(sub)
    args = parser.parse_args(["forecast", "x.json", "y.json"])
    assert args.steps == 3


def test_add_forecast_args_default_top():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_forecast_args(sub)
    args = parser.parse_args(["forecast", "x.json", "y.json"])
    assert args.top == 5


# ---------------------------------------------------------------------------
# _build_histories_from_diffs
# ---------------------------------------------------------------------------

def test_build_histories_counts_per_field():
    snap1 = [make_diff("e1", "cpu", "mem"), make_diff("e2", "cpu")]
    snap2 = [make_diff("e1", "mem")]
    histories = _build_histories_from_diffs([snap1, snap2])
    assert histories["cpu"][0] == 2
    assert histories["mem"][0] == 1
    assert histories["mem"][1] == 1


def test_build_histories_backfills_zeros():
    snap1 = [make_diff("e1", "x")]
    snap2 = [make_diff("e1", "y")]
    histories = _build_histories_from_diffs([snap1, snap2])
    assert len(histories["x"]) == 2
    assert len(histories["y"]) == 2


# ---------------------------------------------------------------------------
# handle_forecast
# ---------------------------------------------------------------------------

def test_handle_forecast_missing_file_returns_2(tmp_path):
    args = build_args(snapshots=[str(tmp_path / "missing.json"), str(tmp_path / "also.json")])
    rc = handle_forecast(args)
    assert rc == 2


def test_handle_forecast_returns_zero_on_success(tmp_path, capsys):
    snap = [
        {"key": "e1", "changes": [{"field": "cpu", "before": "1", "after": "2", "change_type": "modified"}]},
    ]
    f1 = tmp_path / "s1.json"
    f2 = tmp_path / "s2.json"
    f1.write_text(json.dumps(snap))
    f2.write_text(json.dumps(snap))
    args = build_args(snapshots=[str(f1), str(f2)])
    rc = handle_forecast(args)
    assert rc == 0


def test_handle_forecast_no_fields_message(tmp_path, capsys):
    """If no field meets min_history, a friendly message is printed."""
    snap = [{"key": "e1", "changes": []}]
    f1 = tmp_path / "s1.json"
    f1.write_text(json.dumps(snap))
    args = build_args(snapshots=[str(f1)], min_history=2)
    rc = handle_forecast(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No fields" in out
