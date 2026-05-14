"""Tests for logdiff.cli_index."""

from __future__ import annotations

import argparse
from io import StringIO
from typing import List

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.cli_index import add_index_args, handle_index


def make_change(field: str, change_type: str = "modified") -> FieldChange:
    return FieldChange(field=field, before="a", after="b", change_type=change_type)


def make_diff(key: str, *fields: str, change_type: str = "modified") -> EntryDiff:
    changes = [make_change(f, change_type) for f in fields]
    return EntryDiff(key=key, changes=changes)


def build_args(**kwargs) -> argparse.Namespace:
    defaults = {"top": 10, "field": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# add_index_args
# ---------------------------------------------------------------------------

def test_add_index_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_index_args(sub)
    parsed = parser.parse_args(["index"])
    assert parsed is not None


def test_add_index_args_default_top_is_10():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_index_args(sub)
    parsed = parser.parse_args(["index"])
    assert parsed.top == 10


def test_add_index_args_field_default_is_none():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_index_args(sub)
    parsed = parser.parse_args(["index"])
    assert parsed.field is None


# ---------------------------------------------------------------------------
# handle_index
# ---------------------------------------------------------------------------

def test_handle_index_empty_diffs_prints_error(capsys):
    args = build_args()
    handle_index(args, [])
    out = capsys.readouterr().out
    assert "error" in out.lower()


def test_handle_index_prints_top_fields(capsys):
    diffs = [
        make_diff("e1", "status"),
        make_diff("e2", "status"),
        make_diff("e3", "level"),
    ]
    args = build_args(top=5)
    handle_index(args, diffs)
    out = capsys.readouterr().out
    assert "status" in out
    assert "level" in out


def test_handle_index_lookup_known_field(capsys):
    diffs = [make_diff("entry-1", "status", change_type="added")]
    args = build_args(field="status")
    handle_index(args, diffs)
    out = capsys.readouterr().out
    assert "entry-1" in out
    assert "added" in out


def test_handle_index_lookup_unknown_field(capsys):
    diffs = [make_diff("e1", "status")]
    args = build_args(field="nonexistent")
    handle_index(args, diffs)
    out = capsys.readouterr().out
    assert "not found" in out.lower()


def test_handle_index_no_changes_after_index(capsys):
    # Diffs with no changes produce an index but no field entries
    diffs = [EntryDiff(key="e1", changes=[])]
    args = build_args()
    handle_index(args, diffs)
    out = capsys.readouterr().out
    assert "No field changes found" in out
