"""Tests for logdiff.differ_cache."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from logdiff.differ_cache import (
    CACHE_VERSION,
    CacheEntry,
    CacheError,
    _cache_key,
    clear_cache,
    load_cache,
    save_cache,
)


@pytest.fixture()
def tmp_cache(tmp_path):
    return tmp_path / "cache"


@pytest.fixture()
def two_files(tmp_path):
    a = tmp_path / "before.json"
    b = tmp_path / "after.json"
    a.write_text('[{"id": 1}]')
    b.write_text('[{"id": 2}]')
    return str(a), str(b)


# --- CacheEntry ---

def test_cache_entry_roundtrip():
    entry = CacheEntry(key="abc", created_at=1.0, version=CACHE_VERSION, payload={"x": 1})
    assert CacheEntry.from_dict(entry.to_dict()) == entry


# --- _cache_key ---

def test_cache_key_is_deterministic(two_files):
    a, b = two_files
    assert _cache_key(a, b) == _cache_key(a, b)


def test_cache_key_differs_with_extra(two_files):
    a, b = two_files
    assert _cache_key(a, b, "foo") != _cache_key(a, b, "bar")


def test_cache_key_differs_when_file_changes(two_files, tmp_path):
    a, b = two_files
    key_before = _cache_key(a, b)
    Path(a).write_text('[{"id": 99}]')
    # mtime resolution may be coarse — force a detectable change via size
    key_after = _cache_key(a, b)
    # keys should differ because content (and size) changed
    assert key_before != key_after


# --- save_cache / load_cache ---

def test_save_cache_creates_file(tmp_cache):
    entry = save_cache("testkey", {"diffs": []}, cache_dir=tmp_cache)
    assert (tmp_cache / "testkey.json").exists()
    assert entry.key == "testkey"


def test_load_cache_returns_entry(tmp_cache):
    save_cache("k1", {"result": 42}, cache_dir=tmp_cache)
    entry = load_cache("k1", cache_dir=tmp_cache)
    assert entry is not None
    assert entry.payload == {"result": 42}


def test_load_cache_returns_none_for_missing(tmp_cache):
    assert load_cache("nonexistent", cache_dir=tmp_cache) is None


def test_load_cache_rejects_wrong_version(tmp_cache):
    data = {"key": "k2", "created_at": time.time(), "version": 999, "payload": {}}
    (tmp_cache / "k2.json").parent.mkdir(parents=True, exist_ok=True)
    (tmp_cache / "k2.json").write_text(json.dumps(data))
    assert load_cache("k2", cache_dir=tmp_cache) is None


def test_load_cache_raises_on_corrupt_file(tmp_cache):
    tmp_cache.mkdir(parents=True, exist_ok=True)
    (tmp_cache / "bad.json").write_text("not-json{{{")
    with pytest.raises(CacheError):
        load_cache("bad", cache_dir=tmp_cache)


# --- clear_cache ---

def test_clear_cache_removes_entries(tmp_cache):
    save_cache("a", {}, cache_dir=tmp_cache)
    save_cache("b", {}, cache_dir=tmp_cache)
    removed = clear_cache(tmp_cache)
    assert removed == 2
    assert list(tmp_cache.glob("*.json")) == []


def test_clear_cache_on_missing_dir_returns_zero(tmp_path):
    assert clear_cache(tmp_path / "ghost") == 0
