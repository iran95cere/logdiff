"""Tests for logdiff/summarizer.py."""

import pytest

from logdiff.differ import FieldChange, EntryDiff
from logdiff.reporter import DiffReport, build_report
from logdiff.summarizer import (
    SummaryLine,
    TextSummary,
    build_summary,
    format_summary_compact,
)


def make_change(field="status", before="ok", after="error"):
    return FieldChange(field=field, before=before, after=after)


def make_diff(key="req-1", changes=None, status="modified"):
    return EntryDiff(
        key=key,
        status=status,
        changes=changes or [make_change()],
    )


def make_report(**kwargs):
    defaults = dict(
        total_entries=10,
        modified=4,
        added=2,
        removed=1,
        unchanged=3,
        most_changed_fields=["status", "latency"],
    )
    defaults.update(kwargs)
    return DiffReport(**defaults)


# --- SummaryLine ---

def test_summary_line_repr_highlighted():
    line = SummaryLine(label="Modified", value="5", highlight=True)
    assert repr(line) == "[*] Modified: 5"


def test_summary_line_repr_not_highlighted():
    line = SummaryLine(label="Unchanged", value="3", highlight=False)
    assert repr(line) == "[ ] Unchanged: 3"


# --- TextSummary ---

def test_text_summary_render_contains_title():
    summary = TextSummary(lines=[], title="My Report")
    assert "My Report" in summary.render()


def test_text_summary_render_contains_lines():
    lines = [SummaryLine("Modified", "2", highlight=True)]
    summary = TextSummary(lines=lines)
    rendered = summary.render()
    assert "Modified: 2" in rendered


# --- build_summary ---

def test_build_summary_default_title():
    report = make_report()
    summary = build_summary(report)
    assert summary.title == "Diff Summary"


def test_build_summary_custom_title():
    report = make_report()
    summary = build_summary(report, title="Deploy v2.1")
    assert summary.title == "Deploy v2.1"


def test_build_summary_line_count():
    report = make_report()
    summary = build_summary(report)
    assert len(summary.lines) == 7


def test_build_summary_modified_highlighted_when_nonzero():
    report = make_report(modified=3)
    summary = build_summary(report)
    modified_line = next(l for l in summary.lines if l.label == "Modified")
    assert modified_line.highlight is True


def test_build_summary_modified_not_highlighted_when_zero():
    report = make_report(modified=0)
    summary = build_summary(report)
    modified_line = next(l for l in summary.lines if l.label == "Modified")
    assert modified_line.highlight is False


def test_build_summary_change_rate_highlighted_above_50_pct():
    # 6 out of 10 changed => 60%
    report = make_report(total_entries=10, modified=4, added=2, removed=0, unchanged=4)
    summary = build_summary(report)
    rate_line = next(l for l in summary.lines if l.label == "Change rate")
    assert rate_line.highlight is True


def test_build_summary_top_fields_shown():
    report = make_report(most_changed_fields=["status", "latency", "code"])
    summary = build_summary(report)
    fields_line = next(l for l in summary.lines if l.label == "Top changed fields")
    assert "status" in fields_line.value
    assert "latency" in fields_line.value


def test_build_summary_no_changed_fields():
    report = make_report(most_changed_fields=[])
    summary = build_summary(report)
    fields_line = next(l for l in summary.lines if l.label == "Top changed fields")
    assert fields_line.value == "none"


# --- format_summary_compact ---

def test_format_summary_compact_contains_counts():
    report = make_report(total_entries=10, modified=4, added=2, removed=1, unchanged=3)
    result = format_summary_compact(report)
    assert "10 entries" in result
    assert "+2 added" in result
    assert "~4 modified" in result
    assert "-1 removed" in result


def test_format_summary_compact_shows_change_rate():
    report = make_report(total_entries=10, modified=5, added=0, removed=0, unchanged=5)
    result = format_summary_compact(report)
    assert "change rate" in result
