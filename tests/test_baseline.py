"""Tests for logdiff.baseline."""

from __future__ import annotations

import json
import os
import pytest

from logdiff.baseline import (
    Baseline,
    BaselineError,
    delete_baseline,
    list_baselines,
    load_baseline,
    save_baseline,
    _baseline_path,
)


SAMPLE_ENTRIES = [
    {"id": "a1", "status": "ok", "latency": 120},
    {"id": "a2", "status": "error", "latency": 540},
]


def test_save_baseline_creates_file(tmp_path):
    bl = save_baseline("release-1", SAMPLE_ENTRIES, baseline_dir=str(tmp_path))
    expected = tmp_path / "release-1.json"
    assert expected.exists()
    assert bl.name == "release-1"
    assert len(bl.entries) == 2


def test_save_baseline_file_content(tmp_path):
    save_baseline("v1", SAMPLE_ENTRIES, baseline_dir=str(tmp_path))
    with open(tmp_path / "v1.json") as fh:
        data = json.load(fh)
    assert data["name"] == "v1"
    assert data["entries"] == SAMPLE_ENTRIES
    assert "created_at" in data


def test_save_baseline_stores_metadata(tmp_path):
    bl = save_baseline(
        "v2", SAMPLE_ENTRIES, baseline_dir=str(tmp_path), metadata={"env": "prod"}
    )
    assert bl.metadata == {"env": "prod"}


def test_load_baseline_roundtrip(tmp_path):
    save_baseline("snap", SAMPLE_ENTRIES, baseline_dir=str(tmp_path))
    loaded = load_baseline("snap", baseline_dir=str(tmp_path))
    assert loaded.name == "snap"
    assert loaded.entries == SAMPLE_ENTRIES


def test_load_baseline_missing_raises(tmp_path):
    with pytest.raises(BaselineError, match="not found"):
        load_baseline("ghost", baseline_dir=str(tmp_path))


def test_list_baselines_empty_dir(tmp_path):
    assert list_baselines(baseline_dir=str(tmp_path)) == []


def test_list_baselines_nonexistent_dir():
    assert list_baselines(baseline_dir="/tmp/_logdiff_no_such_dir_xyz") == []


def test_list_baselines_returns_names(tmp_path):
    save_baseline("alpha", SAMPLE_ENTRIES, baseline_dir=str(tmp_path))
    save_baseline("beta", SAMPLE_ENTRIES, baseline_dir=str(tmp_path))
    names = list_baselines(baseline_dir=str(tmp_path))
    assert set(names) == {"alpha", "beta"}


def test_delete_baseline_removes_file(tmp_path):
    save_baseline("to-del", SAMPLE_ENTRIES, baseline_dir=str(tmp_path))
    delete_baseline("to-del", baseline_dir=str(tmp_path))
    assert not (tmp_path / "to-del.json").exists()


def test_delete_baseline_missing_raises(tmp_path):
    with pytest.raises(BaselineError, match="not found"):
        delete_baseline("nope", baseline_dir=str(tmp_path))


def test_baseline_from_dict_roundtrip():
    original = Baseline(
        name="x", created_at="2024-01-01T00:00:00+00:00",
        entries=SAMPLE_ENTRIES, metadata={"k": "v"}
    )
    restored = Baseline.from_dict(original.to_dict())
    assert restored.name == original.name
    assert restored.entries == original.entries
    assert restored.metadata == original.metadata


def test_baseline_path_helper(tmp_path):
    path = _baseline_path("my-snap", str(tmp_path))
    assert path.endswith("my-snap.json")
