"""Tests for logdiff.differ_digest and logdiff.cli_digest."""

from __future__ import annotations

import argparse

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_digest import DigestError, DiffDigest, build_digest
from logdiff.cli_digest import add_digest_args, handle_digest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_change(field: str, before=None, after=None, change_type: str = "modified") -> FieldChange:
    return FieldChange(field=field, before=before, after=after, change_type=change_type)


def make_diff(key: str, changes=None) -> EntryDiff:
    return EntryDiff(key=key, changes=changes or [])


# ---------------------------------------------------------------------------
# build_digest
# ---------------------------------------------------------------------------

def test_build_digest_empty_raises():
    with pytest.raises(DigestError, match="empty"):
        build_digest([])


def test_build_digest_entry_count():
    diffs = [make_diff("a"), make_diff("b")]
    digest = build_digest(diffs)
    assert digest.entry_count == 2


def test_build_digest_changed_count():
    diffs = [
        make_diff("a", [make_change("status", "ok", "error")]),
        make_diff("b"),
    ]
    digest = build_digest(diffs)
    assert digest.changed_count == 1


def test_build_digest_field_count():
    diffs = [
        make_diff("a", [make_change("x"), make_change("y")]),
        make_diff("b", [make_change("x")]),
    ]
    digest = build_digest(diffs)
    assert digest.field_count == 2


def test_build_digest_top_fields_ordering():
    diffs = [
        make_diff("a", [make_change("rare")]),
        make_diff("b", [make_change("common"), make_change("rare")]),
        make_diff("c", [make_change("common")]),
    ]
    digest = build_digest(diffs, top_n=1)
    assert digest.top_fields == ["common"]


def test_build_digest_fingerprint_is_string():
    diffs = [make_diff("a", [make_change("f", 1, 2)])]
    digest = build_digest(diffs)
    assert isinstance(digest.fingerprint, str)
    assert len(digest.fingerprint) == 64


def test_build_digest_fingerprint_is_deterministic():
    diffs = [make_diff("a", [make_change("f", 1, 2)])]
    assert build_digest(diffs).fingerprint == build_digest(diffs).fingerprint


def test_build_digest_fingerprint_differs_on_change():
    d1 = [make_diff("a", [make_change("f", 1, 2)])]
    d2 = [make_diff("a", [make_change("f", 1, 3)])]
    assert build_digest(d1).fingerprint != build_digest(d2).fingerprint


def test_build_digest_returns_diff_digest_instance():
    diffs = [make_diff("a")]
    assert isinstance(build_digest(diffs), DiffDigest)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_args(**kwargs) -> argparse.Namespace:
    defaults = {"top": 5, "fingerprint_only": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_digest_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_digest_args(sub)
    parsed = parser.parse_args(["digest"])
    assert parsed is not None


def test_handle_digest_returns_zero(capsys):
    diffs = [make_diff("a", [make_change("f", 1, 2)])]
    rc = handle_digest(build_args(), diffs)
    assert rc == 0


def test_handle_digest_empty_returns_one(capsys):
    rc = handle_digest(build_args(), [])
    assert rc == 1


def test_handle_digest_fingerprint_only(capsys):
    diffs = [make_diff("a", [make_change("f", 1, 2)])]
    rc = handle_digest(build_args(fingerprint_only=True), diffs)
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert len(out) == 64


def test_handle_digest_output_contains_entries(capsys):
    diffs = [make_diff("a"), make_diff("b")]
    handle_digest(build_args(), diffs)
    out = capsys.readouterr().out
    assert "Entries   : 2" in out


def test_handle_digest_no_changes_shows_none(capsys):
    diffs = [make_diff("a")]
    handle_digest(build_args(), diffs)
    out = capsys.readouterr().out
    assert "(none)" in out
