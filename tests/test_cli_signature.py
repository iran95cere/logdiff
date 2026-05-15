"""Tests for logdiff.cli_signature."""

from __future__ import annotations

import argparse
import io
import json
import os

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.cli_signature import add_signature_args, handle_signature


def make_change(field: str, change_type: str = "modified") -> FieldChange:
    return FieldChange(field=field, change_type=change_type, before="a", after="b")


def make_diff(key: str, *changes: FieldChange) -> EntryDiff:
    return EntryDiff(key=key, changes=list(changes))


def build_args(**kwargs) -> argparse.Namespace:
    defaults = {"compare": None, "save": None, "top": 10}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_signature_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_signature_args(sub)
    args = parser.parse_args(["signature"])
    assert args is not None


def test_add_signature_args_default_top():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_signature_args(sub)
    args = parser.parse_args(["signature"])
    assert args.top == 10


def test_handle_signature_returns_zero_on_success():
    diffs = [make_diff("a", make_change("level"))]
    out = io.StringIO()
    rc = handle_signature(build_args(), diffs, out=out)
    assert rc == 0


def test_handle_signature_empty_diffs_returns_one():
    out = io.StringIO()
    rc = handle_signature(build_args(), [], out=out)
    assert rc == 1


def test_handle_signature_output_contains_fingerprint():
    diffs = [make_diff("a", make_change("level"))]
    out = io.StringIO()
    handle_signature(build_args(), diffs, out=out)
    assert "Fingerprint" in out.getvalue()


def test_handle_signature_save_creates_file(tmp_path):
    diffs = [make_diff("a", make_change("level"))]
    save_path = str(tmp_path / "sig.json")
    out = io.StringIO()
    rc = handle_signature(build_args(save=save_path), diffs, out=out)
    assert rc == 0
    assert os.path.exists(save_path)


def test_handle_signature_save_file_contains_fingerprint(tmp_path):
    diffs = [make_diff("a", make_change("level"))]
    save_path = str(tmp_path / "sig.json")
    out = io.StringIO()
    handle_signature(build_args(save=save_path), diffs, out=out)
    with open(save_path) as fh:
        data = json.load(fh)
    assert "fingerprint" in data
    assert len(data["fingerprint"]) == 64


def test_handle_signature_compare_match(tmp_path):
    diffs = [make_diff("a", make_change("level"))]
    save_path = str(tmp_path / "sig.json")
    out = io.StringIO()
    handle_signature(build_args(save=save_path), diffs, out=out)
    out2 = io.StringIO()
    rc = handle_signature(build_args(compare=save_path), diffs, out=out2)
    assert rc == 0
    assert "MATCH" in out2.getvalue()


def test_handle_signature_compare_mismatch(tmp_path):
    diffs_a = [make_diff("a", make_change("level"))]
    diffs_b = [make_diff("a", make_change("status"))]
    save_path = str(tmp_path / "sig.json")
    handle_signature(build_args(save=save_path), diffs_a, out=io.StringIO())
    out = io.StringIO()
    rc = handle_signature(build_args(compare=save_path), diffs_b, out=out)
    assert rc == 2
    assert "DIFF" in out.getvalue()
