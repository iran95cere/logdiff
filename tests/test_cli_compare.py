"""Tests for logdiff.cli_compare."""

import argparse
import json
import pytest

from logdiff.cli_compare import add_compare_args, handle_compare


def make_diff_file(tmp_path, name, entries):
    """Write a minimal diff JSON file and return its path."""
    path = tmp_path / name
    path.write_text(json.dumps(entries), encoding="utf-8")
    return str(path)


def build_args(**kwargs):
    defaults = dict(diff_a="a.json", diff_b="b.json", label_a="A", label_b="B", as_json=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


SAMPLE_ENTRY = {"key": "req-1", "changes": [{"field": "status", "before": "ok", "after": "error", "change_type": "modified"}]}


def test_add_compare_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_compare_args(sub)
    args = parser.parse_args(["compare", "a.json", "b.json"])
    assert args.diff_a == "a.json"
    assert args.diff_b == "b.json"


def test_add_compare_args_default_labels():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_compare_args(sub)
    args = parser.parse_args(["compare", "a.json", "b.json"])
    assert args.label_a == "A"
    assert args.label_b == "B"


def test_handle_compare_returns_zero(tmp_path, capsys):
    path_a = make_diff_file(tmp_path, "a.json", [SAMPLE_ENTRY])
    path_b = make_diff_file(tmp_path, "b.json", [SAMPLE_ENTRY])
    args = build_args(diff_a=path_a, diff_b=path_b)
    rc = handle_compare(args)
    assert rc == 0


def test_handle_compare_text_output(tmp_path, capsys):
    path_a = make_diff_file(tmp_path, "a.json", [SAMPLE_ENTRY])
    path_b = make_diff_file(tmp_path, "b.json", [])
    args = build_args(diff_a=path_a, diff_b=path_b)
    handle_compare(args)
    out = capsys.readouterr().out
    assert "Only in" in out
    assert "Change delta" in out


def test_handle_compare_json_output(tmp_path, capsys):
    path_a = make_diff_file(tmp_path, "a.json", [SAMPLE_ENTRY])
    path_b = make_diff_file(tmp_path, "b.json", [SAMPLE_ENTRY])
    args = build_args(diff_a=path_a, diff_b=path_b, as_json=True)
    handle_compare(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "label_a" in data
    assert "change_delta" in data


def test_handle_compare_missing_file_returns_one(tmp_path):
    args = build_args(diff_a="nonexistent.json", diff_b="also_missing.json")
    rc = handle_compare(args)
    assert rc == 1


def test_handle_compare_error_printed(tmp_path, capsys):
    args = build_args(diff_a="missing.json", diff_b="missing2.json")
    handle_compare(args)
    err = capsys.readouterr().out
    assert "error" in err
