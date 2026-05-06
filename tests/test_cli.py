"""Tests for logdiff.cli — including new --sort / --top flags."""

import json
import pytest
from pathlib import Path
from logdiff.cli import build_parser, main


@pytest.fixture()
def before_file(tmp_path):
    data = [
        {"id": "1", "status": "ok", "latency": 10},
        {"id": "2", "status": "ok", "latency": 20},
        {"id": "3", "status": "ok", "latency": 30},
    ]
    p = tmp_path / "before.json"
    p.write_text(json.dumps(data))
    return str(p)


@pytest.fixture()
def after_file(tmp_path):
    data = [
        {"id": "1", "status": "ok", "latency": 10},
        {"id": "2", "status": "error", "latency": 25},
        {"id": "4", "status": "ok", "latency": 5},
    ]
    p = tmp_path / "after.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_cli_exits_zero_on_success(before_file, after_file):
    assert main([before_file, after_file]) == 0


def test_cli_exits_one_on_missing_file(before_file):
    assert main([before_file, "nonexistent.json"]) == 1


def test_cli_summary_only_flag(before_file, after_file, capsys):
    main([before_file, after_file, "--summary-only"])
    captured = capsys.readouterr()
    # Summary line should mention entry counts
    assert "entries" in captured.out.lower() or "changed" in captured.out.lower()


def test_cli_sort_by_change_count(before_file, after_file):
    assert main([before_file, after_file, "--sort", "change_count"]) == 0


def test_cli_sort_desc(before_file, after_file):
    assert main([before_file, after_file, "--sort", "key", "--sort-desc"]) == 0


def test_cli_top_n(before_file, after_file, capsys):
    assert main([before_file, after_file, "--top", "1"]) == 0


def test_cli_invalid_sort_key_exits_nonzero(before_file, after_file):
    """argparse should reject unknown --sort values."""
    with pytest.raises(SystemExit) as exc_info:
        main([before_file, after_file, "--sort", "invalid_key"])
    assert exc_info.value.code != 0


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["a.json", "b.json"])
    assert args.sort == "key"
    assert args.sort_desc is False
    assert args.top is None
    assert args.summary_only is False
