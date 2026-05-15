"""Tests for logdiff.differ_patch."""

from __future__ import annotations

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_patch import (
    EntryPatch,
    PatchError,
    PatchOp,
    _change_to_op,
    build_patch,
    build_patches,
)


def make_change(field: str, before, after) -> FieldChange:
    return FieldChange(field=field, before=before, after=after)


def make_diff(key: str, changes: list) -> EntryDiff:
    return EntryDiff(key=key, changes=changes)


# --- PatchOp ---

def test_patch_op_repr_with_value():
    op = PatchOp(op="replace", path="/status", value="error")
    assert "replace" in repr(op)
    assert "/status" in repr(op)
    assert "error" in repr(op)


def test_patch_op_repr_without_value():
    op = PatchOp(op="remove", path="/level")
    assert "remove" in repr(op)
    assert "value" not in repr(op)


def test_patch_op_to_dict_include_value():
    op = PatchOp(op="add", path="/host", value="srv1")
    d = op.to_dict()
    assert d == {"op": "add", "path": "/host", "value": "srv1"}


def test_patch_op_to_dict_remove_no_value():
    op = PatchOp(op="remove", path="/host")
    d = op.to_dict()
    assert "value" not in d


# --- _change_to_op ---

def test_change_to_op_add():
    op = _change_to_op(make_change("host", None, "srv1"))
    assert op.op == "add"
    assert op.path == "/host"
    assert op.value == "srv1"


def test_change_to_op_remove():
    op = _change_to_op(make_change("host", "srv1", None))
    assert op.op == "remove"
    assert op.value is None


def test_change_to_op_replace():
    op = _change_to_op(make_change("status", "ok", "error"))
    assert op.op == "replace"
    assert op.value == "error"


def test_change_to_op_nested_field_path():
    op = _change_to_op(make_change("meta.region", "us", "eu"))
    assert op.path == "/meta/region"


# --- build_patch ---

def test_build_patch_returns_entry_patch():
    diff = make_diff("abc", [make_change("level", "info", "warn")])
    patch = build_patch(diff)
    assert isinstance(patch, EntryPatch)
    assert patch.key == "abc"
    assert len(patch.ops) == 1


def test_build_patch_no_changes_is_empty():
    diff = make_diff("abc", [])
    patch = build_patch(diff)
    assert patch.is_empty()


# --- build_patches ---

def test_build_patches_empty_raises():
    with pytest.raises(PatchError):
        build_patches([])


def test_build_patches_skips_unchanged():
    diffs = [
        make_diff("a", [make_change("status", "ok", "error")]),
        make_diff("b", []),
    ]
    patches = build_patches(diffs)
    assert len(patches) == 1
    assert patches[0].key == "a"


def test_build_patches_to_dict_structure():
    diffs = [make_diff("x", [make_change("env", "prod", "staging")])]
    patches = build_patches(diffs)
    d = patches[0].to_dict()
    assert d["key"] == "x"
    assert d["ops"][0]["op"] == "replace"
