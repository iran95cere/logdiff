"""Tests for the logdiff CLI entry point."""

import json
import textwrap
from pathlib import Path

import pytest

from logdiff.cli import main


@pytest.fixture()
def before_file(tmp_path: Path) -> Path:
    data = [
        {"id": "a1", "status": "ok", "latency": 120},
        {"id": "b2", "status": "error", "latency": 300},
    ]
    p = tmp_path / "before.json"
    p.write_text(json.dumps(data))
    return p


@pytest.fixture()
def after_file(tmp_path: Path) -> Path:
    data = [
        {"id": "a1", "status": "ok", "latency": 95},
        {"id": "b2", "status": "ok", "latency": 280},
        {"id": "c3", "status": "ok", "latency": 50},
    ]
    p = tmp_path / "after.json"
    p.write_text(json.dumps(data))
    return p


def test_cli_exits_zero_on_success(before_file: Path, after_file: Path) -> None:
    rc = main([str(before_file), str(after_file)])
    assert rc == 0


def test_cli_exits_one_on_missing_file(tmp_path: Path, after_file: Path) -> None:
    rc = main([str(tmp_path / "nonexistent.json"), str(after_file)])
    assert rc == 1


def test_cli_summary_only_flag(before_file: Path, after_file: Path, capsys) -> None:
    rc = main([str(before_file), str(after_file), "--summary-only"])
    assert rc == 0
    captured = capsys.readouterr()
    # Summary line should mention counts; individual entry headers should not appear
    assert "modified" in captured.out or "added" in captured.out or "removed" in captured.out


def test_cli_no_color_flag(before_file: Path, after_file: Path, capsys) -> None:
    rc = main([str(before_file), str(after_file), "--no-color"])
    assert rc == 0
    captured = capsys.readouterr()
    # ANSI escape sequences should not be present
    assert "\x1b[" not in captured.out


def test_cli_custom_key(tmp_path: Path) -> None:
    before = tmp_path / "b.json"
    after = tmp_path / "a.json"
    before.write_text(json.dumps([{"request_id": "x1", "code": 200}]))
    after.write_text(json.dumps([{"request_id": "x1", "code": 404}]))
    rc = main([str(before), str(after), "--key", "request_id", "--no-color"])
    assert rc == 0
