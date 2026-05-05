"""Tests for logdiff.parser module."""

import json
import textwrap
from pathlib import Path

import pytest

from logdiff.parser import ParseError, parse_log_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_file(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# JSON array format
# ---------------------------------------------------------------------------

def test_parse_json_array(tmp_path):
    fixture = Path("tests/fixtures/sample_array.json")
    entries = parse_log_file(fixture)
    assert len(entries) == 3
    assert entries[0]["level"] == "INFO"
    assert entries[1]["host"] == "db.internal"


def test_parse_json_array_written(tmp_path):
    data = [{"a": 1}, {"b": 2}]
    p = write_file(tmp_path, "log.json", json.dumps(data))
    entries = parse_log_file(p)
    assert entries == data


# ---------------------------------------------------------------------------
# NDJSON format
# ---------------------------------------------------------------------------

def test_parse_ndjson(tmp_path):
    content = textwrap.dedent("""\
        {"level": "INFO", "msg": "ok"}
        {"level": "WARN", "msg": "slow"}
        {"level": "ERROR", "msg": "fail"}
    """)
    p = write_file(tmp_path, "log.ndjson", content)
    entries = parse_log_file(p)
    assert len(entries) == 3
    assert entries[2]["level"] == "ERROR"


def test_parse_ndjson_skips_blank_lines(tmp_path):
    content = '{"x": 1}\n\n{"x": 2}\n'
    p = write_file(tmp_path, "log.ndjson", content)
    entries = parse_log_file(p)
    assert len(entries) == 2


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_file_not_found():
    with pytest.raises(ParseError, match="File not found"):
        parse_log_file("/nonexistent/path/log.json")


def test_empty_file(tmp_path):
    p = write_file(tmp_path, "empty.json", "")
    with pytest.raises(ParseError, match="empty"):
        parse_log_file(p)


def test_invalid_json_array(tmp_path):
    p = write_file(tmp_path, "bad.json", "[{bad json}]")
    with pytest.raises(ParseError, match="Invalid JSON array"):
        parse_log_file(p)


def test_invalid_ndjson_line(tmp_path):
    content = '{"ok": true}\nnot-json\n'
    p = write_file(tmp_path, "bad.ndjson", content)
    with pytest.raises(ParseError, match="line 2"):
        parse_log_file(p)


def test_array_contains_non_object(tmp_path):
    p = write_file(tmp_path, "bad.json", '[{"a": 1}, 42]')
    with pytest.raises(ParseError, match="Entry 1"):
        parse_log_file(p)


def test_ndjson_non_object_line(tmp_path):
    content = '{"a": 1}\n"just a string"\n'
    p = write_file(tmp_path, "bad.ndjson", content)
    with pytest.raises(ParseError, match="line 2"):
        parse_log_file(p)
