"""Tests for logdiff.cli_trend."""

from __future__ import annotations

import argparse
import json
import pytest

from unittest.mock import patch, MagicMock

from logdiff.cli_trend import add_trend_args, handle_trend
from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_trend import TrendError


def make_change(field: str = "status") -> FieldChange:
    return FieldChange(field=field, before="a", after="b", change_type="modified")


def make_diff(*fields: str) -> EntryDiff:
    return EntryDiff(key="e1", changes=[make_change(f) for f in fields])


def build_args(**kwargs) -> argparse.Namespace:
    defaults = {"snapshots": [], "top": 5, "output_json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# --- add_trend_args ---

def test_add_trend_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_trend_args(sub)
    args = parser.parse_args(["trend", "v1:file.json"])
    assert args.snapshots == ["v1:file.json"]


def test_add_trend_args_default_top_is_5():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_trend_args(sub)
    args = parser.parse_args(["trend", "v1:f.json"])
    assert args.top == 5


def test_add_trend_args_json_flag():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_trend_args(sub)
    args = parser.parse_args(["trend", "v1:f.json", "--json"])
    assert args.output_json is True


# --- handle_trend ---

def test_handle_trend_invalid_snapshot_arg_prints_error(capsys):
    args = build_args(snapshots=["no-colon"])
    handle_trend(args)
    out = capsys.readouterr().out
    assert "trend error" in out


def test_handle_trend_text_output(tmp_path, capsys):
    diffs = [make_diff("cpu"), EntryDiff(key="e2", changes=[])]
    snap_file = tmp_path / "v1.json"
    snap_file.write_text(json.dumps([
        {"key": d.key, "changes": [
            {"field": c.field, "before": c.before, "after": c.after, "change_type": c.change_type}
            for c in d.changes
        ]}
        for d in diffs
    ]))

    with patch("logdiff.cli_trend._parse_snapshot_entries") as mock_parse:
        mock_parse.return_value = [{"label": "v1", "diffs": diffs}]
        args = build_args(snapshots=[f"v1:{snap_file}"], top=3, output_json=False)
        handle_trend(args)

    out = capsys.readouterr().out
    assert "Trend Analysis" in out
    assert "v1" in out


def test_handle_trend_json_output(capsys):
    diffs = [make_diff("mem")]
    with patch("logdiff.cli_trend._parse_snapshot_entries") as mock_parse:
        mock_parse.return_value = [{"label": "snap1", "diffs": diffs}]
        args = build_args(snapshots=["snap1:f.json"], top=5, output_json=True)
        handle_trend(args)

    out = capsys.readouterr().out
    data = json.loads(out)
    assert "avg_change_rate" in data
    assert data["points"][0]["label"] == "snap1"
    assert "volatile_fields" in data
