"""Tests for logdiff.cli_snapshot module."""

import argparse
import json
from pathlib import Path

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.reporter import build_report
from logdiff.cli_snapshot import add_snapshot_args, handle_snapshot
from logdiff.snapshot import save_snapshot


def make_change(field="status", before="ok", after="error"):
    return FieldChange(field=field, before=before, after=after)


def make_diff(key="req-1", changes=None):
    return EntryDiff(key=key, changes=changes or [make_change()], added=False, removed=False)


def build_args(**kwargs):
    ns = argparse.Namespace(
        snapshot_cmd=kwargs.get("snapshot_cmd", "save"),
        output=kwargs.get("output", "/tmp/snap.json"),
        snapshot=kwargs.get("snapshot", None),
        fail_on_regression=kwargs.get("fail_on_regression", False),
    )
    return ns


def test_add_snapshot_args_registers_subcommands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_snapshot_args(sub)
    args = parser.parse_args(["snapshot", "save", "--output", "out.json"])
    assert args.snapshot_cmd == "save"
    assert args.output == "out.json"


def test_add_snapshot_args_compare_registers_flags():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_snapshot_args(sub)
    args = parser.parse_args(["snapshot", "compare", "--snapshot", "s.json", "--fail-on-regression"])
    assert args.snapshot_cmd == "compare"
    assert args.fail_on_regression is True


def test_handle_snapshot_save(tmp_path):
    report = build_report([make_diff()])
    out = str(tmp_path / "snap.json")
    args = build_args(snapshot_cmd="save", output=out)
    messages = []
    code = handle_snapshot(args, report, printer=messages.append)
    assert code == 0
    assert Path(out).exists()
    assert any("saved" in m for m in messages)


def test_handle_snapshot_compare_no_regression(tmp_path):
    report = build_report([make_diff()])
    snap = str(tmp_path / "snap.json")
    save_snapshot(report, snap)
    args = build_args(snapshot_cmd="compare", snapshot=snap, fail_on_regression=False)
    messages = []
    code = handle_snapshot(args, report, printer=messages.append)
    assert code == 0


def test_handle_snapshot_compare_regression_no_fail(tmp_path):
    small = build_report([make_diff()])
    snap = str(tmp_path / "snap.json")
    save_snapshot(small, snap)
    big = build_report([make_diff("a"), make_diff("b"), make_diff("c")])
    args = build_args(snapshot_cmd="compare", snapshot=snap, fail_on_regression=False)
    messages = []
    code = handle_snapshot(args, big, printer=messages.append)
    assert code == 0
    assert any("Regression" in m for m in messages)


def test_handle_snapshot_compare_regression_fail_on_flag(tmp_path):
    small = build_report([make_diff()])
    snap = str(tmp_path / "snap.json")
    save_snapshot(small, snap)
    big = build_report([make_diff("a"), make_diff("b"), make_diff("c")])
    args = build_args(snapshot_cmd="compare", snapshot=snap, fail_on_regression=True)
    code = handle_snapshot(args, big, printer=lambda *a, **kw: None)
    assert code == 2


def test_handle_snapshot_missing_file_returns_error():
    report = build_report([make_diff()])
    args = build_args(snapshot_cmd="compare", snapshot="/no/such/file.json", fail_on_regression=False)
    errors = []
    code = handle_snapshot(args, report, printer=lambda msg, **kw: errors.append(msg))
    assert code == 1
