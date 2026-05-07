"""Snapshot comparison: compare current diff results against a saved baseline snapshot."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from logdiff.differ import EntryDiff
from logdiff.reporter import DiffReport


class SnapshotError(Exception):
    """Raised when snapshot operations fail."""


@dataclass
class SnapshotComparison:
    """Result of comparing a current report against a snapshot."""

    snapshot_path: str
    previous_total: int
    current_total: int
    previous_changed: int
    current_changed: int
    new_fields: List[str] = field(default_factory=list)
    removed_fields: List[str] = field(default_factory=list)
    change_rate_delta: float = 0.0

    @property
    def regressed(self) -> bool:
        """True if change rate increased compared to snapshot."""
        return self.change_rate_delta > 0

    @property
    def improved(self) -> bool:
        """True if change rate decreased compared to snapshot."""
        return self.change_rate_delta < 0


def save_snapshot(report: DiffReport, path: str) -> None:
    """Persist a DiffReport summary to a JSON snapshot file."""
    data = {
        "total_entries": report.total_entries,
        "changed_entries": report.changed_entries,
        "added_entries": report.added_entries,
        "removed_entries": report.removed_entries,
        "change_rate": report.change_rate,
        "most_changed_fields": report.most_changed_fields,
    }
    try:
        Path(path).write_text(json.dumps(data, indent=2))
    except OSError as exc:
        raise SnapshotError(f"Failed to write snapshot to {path!r}: {exc}") from exc


def load_snapshot(path: str) -> dict:
    """Load a previously saved snapshot from disk."""
    try:
        raw = Path(path).read_text()
    except FileNotFoundError as exc:
        raise SnapshotError(f"Snapshot file not found: {path!r}") from exc
    except OSError as exc:
        raise SnapshotError(f"Failed to read snapshot {path!r}: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"Invalid JSON in snapshot {path!r}: {exc}") from exc


def compare_with_snapshot(report: DiffReport, snapshot_path: str) -> SnapshotComparison:
    """Compare a live DiffReport against a saved snapshot and return a SnapshotComparison."""
    snap = load_snapshot(snapshot_path)

    prev_fields = set(snap.get("most_changed_fields", []))
    curr_fields = set(report.most_changed_fields)

    return SnapshotComparison(
        snapshot_path=snapshot_path,
        previous_total=snap.get("total_entries", 0),
        current_total=report.total_entries,
        previous_changed=snap.get("changed_entries", 0),
        current_changed=report.changed_entries,
        new_fields=sorted(curr_fields - prev_fields),
        removed_fields=sorted(prev_fields - curr_fields),
        change_rate_delta=round(report.change_rate - snap.get("change_rate", 0.0), 4),
    )
