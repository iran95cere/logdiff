"""Summarizer module: produce human-readable text summaries from DiffReport objects."""

from dataclasses import dataclass
from typing import List, Optional

from logdiff.reporter import DiffReport


@dataclass
class SummaryLine:
    label: str
    value: str
    highlight: bool = False

    def __repr__(self) -> str:
        marker = "*" if self.highlight else " "
        return f"[{marker}] {self.label}: {self.value}"


@dataclass
class TextSummary:
    lines: List[SummaryLine]
    title: str = "Diff Summary"

    def render(self) -> str:
        header = f"=== {self.title} ==="
        body = "\n".join(repr(line) for line in self.lines)
        return f"{header}\n{body}"


def build_summary(report: DiffReport, title: Optional[str] = None) -> TextSummary:
    """Build a TextSummary from a DiffReport."""
    rate_pct = f"{report.change_rate * 100:.1f}%"
    top_fields = ", ".join(report.most_changed_fields[:5]) if report.most_changed_fields else "none"

    lines = [
        SummaryLine("Total entries", str(report.total_entries)),
        SummaryLine("Modified", str(report.modified), highlight=report.modified > 0),
        SummaryLine("Added", str(report.added), highlight=report.added > 0),
        SummaryLine("Removed", str(report.removed), highlight=report.removed > 0),
        SummaryLine("Unchanged", str(report.unchanged)),
        SummaryLine("Change rate", rate_pct, highlight=report.change_rate > 0.5),
        SummaryLine("Top changed fields", top_fields),
    ]

    return TextSummary(lines=lines, title=title or "Diff Summary")


def format_summary_compact(report: DiffReport) -> str:
    """Return a single-line compact summary string."""
    return (
        f"{report.total_entries} entries | "
        f"+{report.added} added | "
        f"~{report.modified} modified | "
        f"-{report.removed} removed | "
        f"{report.change_rate * 100:.1f}% change rate"
    )
