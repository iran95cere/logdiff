"""Tests for logdiff/cli_summarizer.py."""

import argparse
import pytest

from logdiff.differ import FieldChange, EntryDiff
from logdiff.reporter import DiffReport
from logdiff.cli_summarizer import add_summarizer_args, handle_summarizer


def make_report(**kwargs):
    defaults = dict(
        total_entries=8,
        modified=3,
        added=1,
        removed=1,
        unchanged=3,
        most_changed_fields=["status"],
    )
    defaults.update(kwargs)
    return DiffReport(**defaults)


def build_args(**kwargs):
    parser = argparse.ArgumentParser()
    add_summarizer_args(parser)
    defaults = {"summary_title": None, "compact_summary": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_summarizer_args_registers_flags():
    parser = argparse.ArgumentParser()
    add_summarizer_args(parser)
    actions = {a.dest for a in parser._actions}
    assert "summary_title" in actions
    assert "compact_summary" in actions


def test_handle_summarizer_full_contains_header():
    report = make_report()
    args = build_args()
    result = handle_summarizer(args, report)
    assert "Diff Summary" in result


def test_handle_summarizer_custom_title():
    report = make_report()
    args = build_args(summary_title="Release 3.0")
    result = handle_summarizer(args, report)
    assert "Release 3.0" in result


def test_handle_summarizer_compact_flag():
    report = make_report(total_entries=8, modified=3, added=1, removed=1, unchanged=3)
    args = build_args(compact_summary=True)
    result = handle_summarizer(args, report)
    assert "entries" in result
    assert "\n" not in result.strip(), "Compact summary should be a single line"


def test_handle_summarizer_compact_ignores_title():
    report = make_report()
    args = build_args(compact_summary=True, summary_title="Should Be Ignored")
    result = handle_summarizer(args, report)
    assert "Should Be Ignored" not in result


def test_handle_summarizer_full_shows_modified_count():
    report = make_report(modified=7)
    args = build_args()
    result = handle_summarizer(args, report)
    assert "7" in result
