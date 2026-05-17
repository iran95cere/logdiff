"""Tests for logdiff.cli_velocity."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from logdiff.cli_velocity import (
    _parse_snapshot_arg,
    add_velocity_args,
    handle_velocity,
)
from logdiff.differ_velocity import VelocityError


def make_change(field: str) -> dict:
    return {"field": field, "before": "a", "after": "b", "change_type": "modified"}


def make_diff(key: str, fields: list[str]) -> dict:
    return {"key": key, "changes": [make_change(f) for f in fields]}


def make_diff_file(tmp_path: Path, name: str, diffs: list[dict]) -> str:
    p = tmp_path / name
    p.write_text(json.dumps(diffs))
    return str(p)


def build_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "snapshots": [],
        "top": 10,
        "accelerating_only": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_velocity_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_velocity_args(subs)
    parsed = parser.parse_args(["velocity", "s1:file.json"])
    assert parsed.snapshots == ["s1:file.json"]


def test_add_velocity_args_default_top():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_velocity_args(subs)
    parsed = parser.parse_args(["velocity", "s1:f.json"])
    assert parsed.top == 10


def test_parse_snapshot_arg_valid():
    label, path = _parse_snapshot_arg("v1:/tmp/diffs.json")
    assert label == "v1"
    assert path == "/tmp/diffs.json"


def test_parse_snapshot_arg_missing_colon_raises():
    with pytest.raises(VelocityError):
        _parse_snapshot_arg("nodivider")


def test_handle_velocity_returns_zero(tmp_path):
    f1 = make_diff_file(tmp_path, "s1.json", [make_diff("e1", ["status"])])
    f2 = make_diff_file(tmp_path, "s2.json", [make_diff("e1", ["status", "level"])])
    args = build_args(snapshots=[f"s1:{f1}", f"s2:{f2}"])
    assert handle_velocity(args) == 0


def test_handle_velocity_missing_file_returns_one(tmp_path):
    args = build_args(snapshots=["s1:/nonexistent/path.json"])
    assert handle_velocity(args) == 1


def test_handle_velocity_accelerating_only_filters(tmp_path, capsys):
    f1 = make_diff_file(tmp_path, "s1.json", [make_diff("e1", ["status"])])
    f2 = make_diff_file(tmp_path, "s2.json", [make_diff("e1", ["status", "status", "level"])])
    args = build_args(snapshots=[f"s1:{f1}", f"s2:{f2}"], accelerating_only=True)
    rc = handle_velocity(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "status" in out


def test_handle_velocity_no_matching_fields_prints_message(tmp_path, capsys):
    # Single snapshot means is_accelerating is always False
    f1 = make_diff_file(tmp_path, "s1.json", [make_diff("e1", ["status"])])
    args = build_args(snapshots=[f"s1:{f1}"], accelerating_only=True)
    rc = handle_velocity(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No fields" in out
