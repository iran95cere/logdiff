"""Tests for logdiff.cli_trace."""
import json
import argparse
import pytest

from logdiff.differ_trace import TraceError
from logdiff.cli_trace import (
    add_trace_args,
    _parse_snapshot_arg,
    _load_diffs_from_file,
    handle_trace,
)


def make_diff_file(tmp_path, name, entries):
    p = tmp_path / name
    p.write_text(json.dumps(entries))
    return str(p)


def build_args(**kwargs):
    base = dict(snapshots=[], field=None, unstable_only=False)
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_add_trace_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_trace_args(sub)
    args = parser.parse_args(["trace", "v1:/dev/null"])
    assert hasattr(args, "func")


def test_add_trace_args_default_flags():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_trace_args(sub)
    args = parser.parse_args(["trace", "v1:f.json"])
    assert args.field is None
    assert args.unstable_only is False


def test_parse_snapshot_arg_valid():
    label, path = _parse_snapshot_arg("v1:/tmp/file.json")
    assert label == "v1"
    assert path == "/tmp/file.json"


def test_parse_snapshot_arg_missing_colon_raises():
    with pytest.raises(TraceError):
        _parse_snapshot_arg("nodivider")


def test_load_diffs_from_file(tmp_path):
    data = [
        {"key": "a", "changes": [{"field": "x", "before": 1, "after": 2, "change_type": "modified"}]}
    ]
    path = make_diff_file(tmp_path, "d.json", data)
    diffs = _load_diffs_from_file(path)
    assert len(diffs) == 1
    assert diffs[0].key == "a"
    assert diffs[0].changes[0].field == "x"


def test_handle_trace_returns_zero(tmp_path, capsys):
    data = [
        {"key": "a", "changes": [{"field": "status", "before": "ok", "after": "err", "change_type": "modified"}]}
    ]
    path = make_diff_file(tmp_path, "snap.json", data)
    args = build_args(snapshots=[f"v1:{path}"])
    rc = handle_trace(args)
    assert rc == 0


def test_handle_trace_output_contains_field(tmp_path, capsys):
    data = [
        {"key": "a", "changes": [{"field": "level", "before": "info", "after": "warn", "change_type": "modified"}]}
    ]
    path = make_diff_file(tmp_path, "snap.json", data)
    args = build_args(snapshots=[f"v1:{path}"])
    handle_trace(args)
    out = capsys.readouterr().out
    assert "level" in out


def test_handle_trace_field_filter(tmp_path, capsys):
    data = [
        {"key": "a", "changes": [
            {"field": "level", "before": "info", "after": "warn", "change_type": "modified"},
            {"field": "code", "before": 200, "after": 404, "change_type": "modified"},
        ]}
    ]
    path = make_diff_file(tmp_path, "snap.json", data)
    args = build_args(snapshots=[f"v1:{path}"], field="level")
    handle_trace(args)
    out = capsys.readouterr().out
    assert "level" in out
    assert "code" not in out


def test_handle_trace_no_match_prints_message(tmp_path, capsys):
    data = [
        {"key": "a", "changes": [{"field": "x", "before": 1, "after": 1, "change_type": "modified"}]}
    ]
    path = make_diff_file(tmp_path, "snap.json", data)
    args = build_args(snapshots=[f"v1:{path}"], field="nonexistent")
    rc = handle_trace(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "No matching" in out
