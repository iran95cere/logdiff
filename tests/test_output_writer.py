"""Tests for logdiff.output_writer."""

import json
from pathlib import Path

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.reporter import build_report
from logdiff.output_writer import write_output, UnsupportedFormatError


def make_diff(key, field, old, new):
    change = FieldChange(field=field, old_value=old, new_value=new, change_type="modified")
    return EntryDiff(key=key, changes=[change])


@pytest.fixture
def diffs():
    return [make_diff("req-1", "status", 200, 500)]


@pytest.fixture
def report(diffs):
    return build_report(diffs, total=2)


def test_write_output_json_to_stdout(diffs, report, capsys):
    write_output(report, diffs, fmt="json")
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["summary"]["modified"] == 1


def test_write_output_csv_to_stdout(diffs, report, capsys):
    write_output(report, diffs, fmt="csv")
    captured = capsys.readouterr()
    assert "key,field,change_type" in captured.out
    assert "req-1" in captured.out


def test_write_output_markdown_to_stdout(diffs, report, capsys):
    write_output(report, diffs, fmt="markdown")
    captured = capsys.readouterr()
    assert "## Summary" in captured.out


def test_write_output_json_to_file(tmp_path, diffs, report):
    out_file = tmp_path / "result.json"
    write_output(report, diffs, fmt="json", output_path=str(out_file))
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "entries" in data


def test_write_output_csv_to_file(tmp_path, diffs, report):
    out_file = tmp_path / "result.csv"
    write_output(report, diffs, fmt="csv", output_path=str(out_file))
    content = out_file.read_text()
    assert "status" in content


def test_write_output_markdown_to_file(tmp_path, diffs, report):
    out_file = tmp_path / "result.md"
    write_output(report, diffs, fmt="markdown", output_path=str(out_file))
    content = out_file.read_text()
    assert "# Log Diff Report" in content


def test_write_output_creates_parent_dirs(tmp_path, diffs, report):
    out_file = tmp_path / "nested" / "deep" / "result.json"
    write_output(report, diffs, fmt="json", output_path=str(out_file))
    assert out_file.exists()


def test_write_output_unsupported_format_raises(diffs, report):
    with pytest.raises(UnsupportedFormatError, match="xml"):
        write_output(report, diffs, fmt="xml")


def test_write_output_case_insensitive(diffs, report, capsys):
    write_output(report, diffs, fmt="JSON")
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "summary" in data
