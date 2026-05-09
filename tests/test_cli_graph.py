"""Tests for logdiff.cli_graph."""

import argparse
from types import SimpleNamespace
from typing import List

from logdiff.differ import EntryDiff, FieldChange
from logdiff.cli_graph import add_graph_args, handle_graph


def make_change(field: str) -> FieldChange:
    return FieldChange(field=field, before="old", after="new")


def make_diff(key: str, *fields: str) -> EntryDiff:
    return EntryDiff(key=key, status="modified", changes=[make_change(f) for f in fields])


def build_args(**kwargs) -> argparse.Namespace:
    defaults = {"top": 5, "edges": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_graph_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_graph_args(subparsers)
    args = parser.parse_args(["graph"])
    assert hasattr(args, "top")


def test_add_graph_args_default_top_is_5():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_graph_args(subparsers)
    args = parser.parse_args(["graph"])
    assert args.top == 5


def test_add_graph_args_edges_flag():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_graph_args(subparsers)
    args = parser.parse_args(["graph", "--edges"])
    assert args.edges is True


def test_handle_graph_empty_diffs_returns_one(capsys):
    args = build_args()
    code = handle_graph(args, [])
    assert code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.out


def test_handle_graph_prints_top_fields(capsys):
    diffs = [
        make_diff("e1", "level", "status"),
        make_diff("e2", "level"),
    ]
    args = build_args(top=3)
    code = handle_graph(args, diffs)
    assert code == 0
    captured = capsys.readouterr()
    assert "level" in captured.out


def test_handle_graph_edges_flag_prints_edges(capsys):
    diffs = [make_diff("e1", "a", "b")]
    args = build_args(edges=True)
    code = handle_graph(args, diffs)
    assert code == 0
    captured = capsys.readouterr()
    assert "a" in captured.out
    assert "b" in captured.out


def test_handle_graph_no_changes_prints_message(capsys):
    diffs = [make_diff("e1")]  # no fields
    args = build_args(top=5)
    code = handle_graph(args, diffs)
    assert code == 0
    captured = capsys.readouterr()
    assert "No field changes" in captured.out


def test_handle_graph_edges_no_edges_message(capsys):
    diffs = [make_diff("e1")]  # single field, no co-changes
    args = build_args(edges=True)
    code = handle_graph(args, diffs)
    assert code == 0
    captured = capsys.readouterr()
    assert "No co-change edges" in captured.out
