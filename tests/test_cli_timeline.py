"""Tests for logdiff.cli_timeline."""

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from logdiff.cli_timeline import add_timeline_args, handle_timeline, _parse_snapshot_arg
from logdiff.differ import EntryDiff, FieldChange


def make_change() -> FieldChange:
    return FieldChange(field="status", before="ok", after="error")


def make_diff(key: str = "r1") -> EntryDiff:
    return EntryDiff(key=key, changes=[make_change()])


def build_args(**kwargs) -> argparse.Namespace:
    defaults = dict(snapshots=["v1:a.json", "v2:b.json"], key="id", peak=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# --- _parse_snapshot_arg ---

def test_parse_snapshot_arg_valid():
    label, path = _parse_snapshot_arg("v1:/tmp/a.json")
    assert label == "v1"
    assert path == "/tmp/a.json"


def test_parse_snapshot_arg_missing_colon_raises():
    with pytest.raises(ValueError, match="LABEL:FILE"):
        _parse_snapshot_arg("no-colon-here")


# --- add_timeline_args ---

def test_add_timeline_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_timeline_args(sub)
    args = parser.parse_args(["timeline", "--snapshots", "v1:a.json", "v2:b.json"])
    assert args.snapshots == ["v1:a.json", "v2:b.json"]


def test_add_timeline_args_default_key():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_timeline_args(sub)
    args = parser.parse_args(["timeline", "--snapshots", "v1:a.json", "v2:b.json"])
    assert args.key == "id"


def test_add_timeline_args_peak_flag():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_timeline_args(sub)
    args = parser.parse_args(["timeline", "--snapshots", "v1:a.json", "v2:b.json", "--peak"])
    assert args.peak is True


# --- handle_timeline ---

def test_handle_timeline_single_snapshot_exits_early(capsys):
    args = build_args(snapshots=["v1:a.json"])
    handle_timeline(args)
    out = capsys.readouterr().out
    assert "At least two" in out


def test_handle_timeline_prints_slices(tmp_path, capsys):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps([{"id": "r1", "status": "ok"}]))
    b.write_text(json.dumps([{"id": "r1", "status": "error"}]))
    args = build_args(snapshots=[f"v1:{a}", f"v2:{b}"])
    handle_timeline(args)
    out = capsys.readouterr().out
    assert "v1->v2" in out


def test_handle_timeline_peak_flag(tmp_path, capsys):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps([{"id": "r1", "status": "ok"}]))
    b.write_text(json.dumps([{"id": "r1", "status": "error"}]))
    args = build_args(snapshots=[f"v1:{a}", f"v2:{b}"], peak=True)
    handle_timeline(args)
    out = capsys.readouterr().out
    assert "Peak" in out


def test_handle_timeline_bad_file_prints_error(tmp_path, capsys):
    args = build_args(snapshots=["v1:/nonexistent/a.json", "v2:/nonexistent/b.json"])
    handle_timeline(args)
    out = capsys.readouterr().out
    assert "Failed to load" in out
