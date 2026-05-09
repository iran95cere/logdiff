"""Timeline module: group and order diffs across multiple snapshots in time."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logdiff.differ import EntryDiff


class TimelineError(Exception):
    """Raised when timeline construction fails."""


@dataclass
class TimelineSlice:
    """A single point-in-time snapshot of diffs."""

    label: str
    diffs: List[EntryDiff]

    @property
    def change_count(self) -> int:
        return sum(1 for d in self.diffs if d.has_changes())

    @property
    def entry_count(self) -> int:
        return len(self.diffs)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TimelineSlice(label={self.label!r}, entries={self.entry_count}, changes={self.change_count})"


@dataclass
class Timeline:
    """Ordered collection of TimelineSlice objects."""

    slices: List[TimelineSlice] = field(default_factory=list)

    @property
    def labels(self) -> List[str]:
        return [s.label for s in self.slices]

    def get_slice(self, label: str) -> Optional[TimelineSlice]:
        for s in self.slices:
            if s.label == label:
                return s
        return None

    def change_counts(self) -> Dict[str, int]:
        return {s.label: s.change_count for s in self.slices}

    def peak_slice(self) -> Optional[TimelineSlice]:
        """Return the slice with the most changes."""
        if not self.slices:
            return None
        return max(self.slices, key=lambda s: s.change_count)


def build_timeline(labeled_diffs: Dict[str, List[EntryDiff]]) -> Timeline:
    """Build a Timeline from an ordered mapping of label -> diffs.

    Args:
        labeled_diffs: dict mapping string labels (e.g. deploy version or date)
                       to a list of EntryDiff objects. Insertion order is preserved.

    Returns:
        A Timeline instance with one TimelineSlice per label.

    Raises:
        TimelineError: if labeled_diffs is empty.
    """
    if not labeled_diffs:
        raise TimelineError("Cannot build a timeline from an empty mapping.")

    slices = [
        TimelineSlice(label=label, diffs=diffs)
        for label, diffs in labeled_diffs.items()
    ]
    return Timeline(slices=slices)
