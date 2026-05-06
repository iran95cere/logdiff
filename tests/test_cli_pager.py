"""Tests for logdiff.cli_pager."""

import argparse
from unittest.mock import patch

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.cli_pager import add_pager_args, handle_pager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_change(field="status", old="ok", new="error"):
    return FieldChange(field=field, old_value=old, new_value=new)


def make_diff(key: str, changed: bool = True) -> EntryDiff:
    changes = [make_change()] if changed else []
    return EntryDiff(key=key, before={"id": key}, after={"id": key}, changes=changes)


def build_args(**kwargs) -> argparse.Namespace:
    defaults = {"page": None, "page_size": 5, "all_pages": False, "changed_only": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


DIFFS = [make_diff(str(i)) for i in range(12)]


# ---------------------------------------------------------------------------
# add_pager_args()
# ---------------------------------------------------------------------------

def test_add_pager_args_registers_flags():
    parser = argparse.ArgumentParser()
    add_pager_args(parser)
    args = parser.parse_args(["--page", "2", "--page-size", "10"])
    assert args.page == 2
    assert args.page_size == 10


def test_add_pager_args_all_pages_flag():
    parser = argparse.ArgumentParser()
    add_pager_args(parser)
    args = parser.parse_args(["--all-pages"])
    assert args.all_pages is True


def test_add_pager_args_defaults():
    parser = argparse.ArgumentParser()
    add_pager_args(parser)
    args = parser.parse_args([])
    assert args.page is None
    assert args.page_size == 20
    assert args.all_pages is False


# ---------------------------------------------------------------------------
# handle_pager()
# ---------------------------------------------------------------------------

def test_handle_pager_returns_zero_on_success(capsys):
    args = build_args(page=1, page_size=5)
    code = handle_pager(DIFFS, args, color=False)
    assert code == 0


def test_handle_pager_prints_page_header(capsys):
    args = build_args(page=1, page_size=5)
    handle_pager(DIFFS, args, color=False)
    out = capsys.readouterr().out
    assert "Page 1 of" in out


def test_handle_pager_all_pages_prints_multiple_headers(capsys):
    args = build_args(all_pages=True, page_size=5)
    handle_pager(DIFFS, args, color=False)
    out = capsys.readouterr().out
    assert out.count("Page") >= 3  # 12 items / 5 per page = 3 pages


def test_handle_pager_invalid_page_returns_one(capsys):
    args = build_args(page=999, page_size=5)
    code = handle_pager(DIFFS, args, color=False)
    assert code == 1
    err = capsys.readouterr().err
    assert "pagination error" in err


def test_handle_pager_invalid_page_size_returns_one(capsys):
    args = build_args(page=1, page_size=0)
    code = handle_pager(DIFFS, args, color=False)
    assert code == 1


def test_handle_pager_changed_only_filters(capsys):
    mixed = [make_diff(str(i), changed=(i % 2 == 0)) for i in range(10)]
    args = build_args(page=1, page_size=10, changed_only=True)
    code = handle_pager(mixed, args, color=False)
    assert code == 0
    out = capsys.readouterr().out
    assert "Page 1 of 1" in out
