"""Reporter module: aggregates diff results into a structured summary report."""

from dataclasses import dataclass, field
from typing import List, Optional

from logdiff.differ import EntryDiff, FieldChange


@dataclass
class DiffReport:
    """Aggregated report of all diffs between two log files."""

    total_entries: int = 0
    added: int = 0
    removed: int = 0
    modified: int = 0
    unchanged: int = 0
    diffs: List[EntryDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return (self.added + self.removed + self.modified) > 0

    @property
    def change_rate(self) -> float:
        if self.total_entries == 0:
            return 0.0
        return round((self.added + self.removed + self.modified) / self.total_entries, 4)

    def most_changed_fields(self, top_n: int = 5) -> List[tuple]:
        """Return the top N fields by change frequency."""
        counts: dict = {}
        for diff in self.diffs:
            for change in diff.changes:
                counts[change.field] = counts.get(change.field, 0) + 1
        sorted_fields = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_fields[:top_n]


def build_report(diffs: List[EntryDiff], total_before: int, total_after: int) -> DiffReport:
    """Build a DiffReport from a list of EntryDiff objects."""
    report = DiffReport()
    report.total_entries = max(total_before, total_after)
    report.diffs = diffs

    for diff in diffs:
        if diff.is_added:
            report.added += 1
        elif diff.is_removed:
            report.removed += 1
        elif diff.has_changes:
            report.modified += 1
        else:
            report.unchanged += 1

    return report
