"""Tests for logdiff.cli_baseline."""

from __future__ import annotations

import argparse
import json
import os
import pytest

from logdiff.cli_baseline import add_baseline_args, handle_baseline
from logdiff.baseline import save_baseline


SAMPLE_ENTRIES = [{"id": "e1", "status": "ok"}, {"id": "e2", "status": "warn"}]


def build_args(baseline_dir: str, *argv: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_baseline_args(parser)
    return parser.parse_args(list(argv) + ["--baseline-dir", baseline_dir])


def make_log_file(tmp_path, entries=None):
    entries = entries or SAMPLE_ENTRIES
    p = tmp_path / "log.json"
    p.write_text(json.dumps(entries))
    return str(p)


def test_add_baseline_args_registers_subcommands():
    parser = argparse.ArgumentParser()
    add_baseline_args(parser)
    # Ensure sub-commands exist without error
    args = parser.parse_args(["list", "--baseline-dir", "/tmp"])
    assert args.baseline_cmd == "list"


def test_handle_baseline_save(tmp_path, capsys):
    log = make_log_file(tmp_path)
    args = build_args(str(tmp_path), "save", "snap1", log)
    code = handle_baseline(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "snap1" in out
    assert "2 entries" in out


def test_handle_baseline_list(tmp_path, capsys):
    save_baseline("bl-a", SAMPLE_ENTRIES, baseline_dir=str(tmp_path))
    save_baseline("bl-b", SAMPLE_ENTRIES, baseline_dir=str(tmp_path))
    args = build_args(str(tmp_path), "list")
    code = handle_baseline(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "bl-a" in out
    assert "bl-b" in out


def test_handle_baseline_list_empty(tmp_path, capsys):
    args = build_args(str(tmp_path), "list")
    code = handle_baseline(args)
    assert code == 0
    assert "No baselines" in capsys.readouterr().out


def test_handle_baseline_show(tmp_path, capsys):
    save_baseline("snap2", SAMPLE_ENTRIES, baseline_dir=str(tmp_path))
    args = build_args(str(tmp_path), "show", "snap2")
    code = handle_baseline(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "snap2" in out


def test_handle_baseline_delete(tmp_path, capsys):
    save_baseline("snap3", SAMPLE_ENTRIES, baseline_dir=str(tmp_path))
    args = build_args(str(tmp_path), "delete", "snap3")
    code = handle_baseline(args)
    assert code == 0
    assert "snap3" in capsys.readouterr().out


def test_handle_baseline_delete_missing_returns_1(tmp_path, capsys):
    args = build_args(str(tmp_path), "delete", "ghost")
    code = handle_baseline(args)
    assert code == 1
    assert "baseline error" in capsys.readouterr().err


def test_handle_baseline_no_cmd_returns_2(tmp_path, capsys):
    args = argparse.Namespace(baseline_cmd=None, baseline_dir=str(tmp_path))
    code = handle_baseline(args)
    assert code == 2
