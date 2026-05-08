"""Tests for logdiff.alias and logdiff.cli_alias."""

from __future__ import annotations

import json
import argparse
import pytest

from logdiff.alias import (
    Alias,
    AliasError,
    AliasRegistry,
    load_aliases,
    resolve_fields,
    save_aliases,
)
from logdiff.cli_alias import add_alias_args, handle_alias


# ---------------------------------------------------------------------------
# AliasRegistry unit tests
# ---------------------------------------------------------------------------

def test_add_alias_stores_entry():
    reg = AliasRegistry()
    alias = reg.add("perf", ["latency_ms", "cpu_pct"])
    assert alias.name == "perf"
    assert alias.fields == ["latency_ms", "cpu_pct"]


def test_add_alias_empty_name_raises():
    reg = AliasRegistry()
    with pytest.raises(AliasError, match="empty"):
        reg.add("", ["field"])


def test_add_alias_no_fields_raises():
    reg = AliasRegistry()
    with pytest.raises(AliasError, match="at least one field"):
        reg.add("empty", [])


def test_get_missing_alias_raises():
    reg = AliasRegistry()
    with pytest.raises(AliasError, match="not found"):
        reg.get("nonexistent")


def test_remove_alias():
    reg = AliasRegistry()
    reg.add("x", ["a"])
    reg.remove("x")
    with pytest.raises(AliasError):
        reg.get("x")


def test_remove_missing_raises():
    reg = AliasRegistry()
    with pytest.raises(AliasError, match="not found"):
        reg.remove("ghost")


def test_list_all_sorted():
    reg = AliasRegistry()
    reg.add("zzz", ["z"])
    reg.add("aaa", ["a"])
    names = [a.name for a in reg.list_all()]
    assert names == ["aaa", "zzz"]


def test_roundtrip_to_from_dict():
    reg = AliasRegistry()
    reg.add("perf", ["latency_ms"], description="performance fields")
    restored = AliasRegistry.from_dict(reg.to_dict())
    alias = restored.get("perf")
    assert alias.fields == ["latency_ms"]
    assert alias.description == "performance fields"


def test_save_and_load_aliases(tmp_path):
    path = str(tmp_path / "aliases.json")
    reg = AliasRegistry()
    reg.add("errors", ["error_code", "error_msg"])
    save_aliases(reg, path)
    loaded = load_aliases(path)
    alias = loaded.get("errors")
    assert alias.fields == ["error_code", "error_msg"]


def test_load_aliases_missing_file_raises(tmp_path):
    with pytest.raises(AliasError, match="not found"):
        load_aliases(str(tmp_path / "missing.json"))


def test_resolve_fields_expands_alias():
    reg = AliasRegistry()
    reg.add("perf", ["latency_ms", "cpu_pct"])
    result = resolve_fields(["perf", "status"], reg)
    assert result == ["latency_ms", "cpu_pct", "status"]


def test_resolve_fields_passthrough_unknown():
    reg = AliasRegistry()
    result = resolve_fields(["plain_field"], reg)
    assert result == ["plain_field"]


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def build_args(alias_cmd: str, **kwargs) -> argparse.Namespace:
    defaults = {"alias_cmd": alias_cmd, "file": ".aliases_test.json"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_alias_args_registers_subcommand():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_alias_args(subs)
    parsed = parser.parse_args(["alias", "list", "--file", "x.json"])
    assert parsed.alias_cmd == "list"


def test_handle_alias_add(tmp_path):
    path = str(tmp_path / "aliases.json")
    args = build_args("add", name="perf", fields=["latency_ms"], desc=None, file=path)
    rc = handle_alias(args)
    assert rc == 0
    loaded = load_aliases(path)
    assert loaded.get("perf").fields == ["latency_ms"]


def test_handle_alias_remove(tmp_path):
    path = str(tmp_path / "aliases.json")
    reg = AliasRegistry()
    reg.add("x", ["a"])
    save_aliases(reg, path)
    args = build_args("remove", name="x", file=path)
    rc = handle_alias(args)
    assert rc == 0


def test_handle_alias_list_empty(tmp_path, capsys):
    path = str(tmp_path / "aliases.json")
    args = build_args("list", file=path)
    rc = handle_alias(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No aliases" in out


def test_handle_alias_list_shows_entries(tmp_path, capsys):
    path = str(tmp_path / "aliases.json")
    reg = AliasRegistry()
    reg.add("perf", ["latency_ms", "cpu_pct"], description="perf fields")
    save_aliases(reg, path)
    args = build_args("list", file=path)
    handle_alias(args)
    out = capsys.readouterr().out
    assert "perf" in out
    assert "latency_ms" in out
