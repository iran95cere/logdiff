"""Tests for logdiff.exporter."""

import csv
import io
import json

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.reporter import DiffReport, build_report
from logdiff.exporter import export_json, export_csv, export_markdown


def make_change(field, old=None, new=None, change_type="modified"):
    return FieldChange(field=field, old_value=old, new_value=new, change_type=change_type)


def make_diff(key, changes):
    return EntryDiff(key=key, changes=changes)


@pytest.fixture
def sample_diffs():
    return [
        make_diff("req-1", [make_change("status", 200, 500)]),
        make_diff("req-2", [make_change("latency", 10, 20), make_change("region", "us", "eu")]),
    ]


@pytest.fixture
def sample_report(sample_diffs):
    return build_report(sample_diffs, total=4)


def test_export_json_structure(sample_diffs, sample_report):
    result = export_json(sample_report, sample_diffs)
    data = json.loads(result)
    assert "summary" in data
    assert "entries" in data
    assert data["summary"]["total"] == 4
    assert data["summary"]["modified"] == 2
    assert len(data["entries"]) == 2


def test_export_json_entry_fields(sample_diffs, sample_report):
    result = export_json(sample_report, sample_diffs)
    data = json.loads(result)
    first = data["entries"][0]
    assert first["key"] == "req-1"
    assert first["changes"][0]["field"] == "status"
    assert first["changes"][0]["old_value"] == 200
    assert first["changes"][0]["new_value"] == 500


def test_export_json_change_rate(sample_diffs, sample_report):
    result = export_json(sample_report, sample_diffs)
    data = json.loads(result)
    assert data["summary"]["change_rate"] == pytest.approx(0.5)


def test_export_csv_headers(sample_diffs):
    result = export_csv(sample_diffs)
    reader = csv.reader(io.StringIO(result))
    headers = next(reader)
    assert headers == ["key", "field", "change_type", "old_value", "new_value"]


def test_export_csv_row_count(sample_diffs):
    result = export_csv(sample_diffs)
    reader = csv.reader(io.StringIO(result))
    rows = list(reader)
    # 1 header + 3 change rows
    assert len(rows) == 4


def test_export_csv_values(sample_diffs):
    result = export_csv(sample_diffs)
    reader = csv.reader(io.StringIO(result))
    next(reader)  # skip header
    first_row = next(reader)
    assert first_row[0] == "req-1"
    assert first_row[1] == "status"
    assert first_row[2] == "modified"


def test_export_markdown_contains_summary(sample_diffs, sample_report):
    result = export_markdown(sample_report, sample_diffs)
    assert "## Summary" in result
    assert "| Total entries | 4 |" in result
    assert "| Modified | 2 |" in result


def test_export_markdown_contains_entries(sample_diffs, sample_report):
    result = export_markdown(sample_report, sample_diffs)
    assert "`req-1`" in result
    assert "`status`" in result


def test_export_markdown_empty_diffs(sample_report):
    result = export_markdown(sample_report, [])
    assert "## Summary" in result
    assert "## Changed Entries" not in result
