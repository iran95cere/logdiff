"""Spotlight module: surface the most noteworthy field changes across a diff set."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from logdiff.differ import EntryDiff, FieldChange


class SpotlightError(Exception):
    """Raised when spotlight analysis cannot be performed."""


@dataclass
class SpotlightEntry:
    """A single noteworthy change surfaced by the spotlight."""

    entry_key: str
    field: str
    change: FieldChange
    reason: str
    score: float

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SpotlightEntry(key={self.entry_key!r}, field={self.field!r}, "
            f"reason={self.reason!r}, score={self.score:.2f})"
        )


@dataclass
class SpotlightResult:
    """Collection of spotlight entries produced from a diff set."""

    entries: List[SpotlightEntry] = field(default_factory=list)
    total_scanned: int = 0

    @property
    def top(self) -> Optional[SpotlightEntry]:
        """Return the highest-scoring spotlight entry, or None."""
        return self.entries[0] if self.entries else None


_STATUS_FIELD = "status"
_HIGH_SCORE_THRESHOLD = 2.0


def _score_change(field_name: str, change: FieldChange) -> float:
    """Assign a numeric importance score to a single field change."""
    score = 1.0
    if change.change_type == "removed":
        score += 1.0
    elif change.change_type == "added":
        score += 0.5
    if field_name == _STATUS_FIELD:
        score += 1.5
    if change.before is not None and change.after is not None:
        try:
            if float(change.after) > float(change.before) * 2:
                score += 0.5
        except (TypeError, ValueError):
            pass
    return score


def _reason_for(field_name: str, change: FieldChange) -> str:
    """Return a human-readable reason string for why this change is notable."""
    if field_name == _STATUS_FIELD:
        return f"status transition: {change.before!r} → {change.after!r}"
    if change.change_type == "removed":
        return f"field '{field_name}' was removed"
    if change.change_type == "added":
        return f"field '{field_name}' is newly present"
    return f"field '{field_name}' changed: {change.before!r} → {change.after!r}"


def build_spotlight(
    diffs: List[EntryDiff],
    top_n: int = 10,
    min_score: float = 1.0,
) -> SpotlightResult:
    """Analyse *diffs* and return the most noteworthy field-level changes.

    Args:
        diffs: List of EntryDiff objects to scan.
        top_n: Maximum number of spotlight entries to return.
        min_score: Minimum score required for an entry to be included.

    Returns:
        A SpotlightResult sorted by descending score.

    Raises:
        SpotlightError: If *diffs* is empty.
    """
    if not diffs:
        raise SpotlightError("Cannot build spotlight from an empty diff list.")

    candidates: List[SpotlightEntry] = []
    for diff in diffs:
        for field_name, change in diff.changes.items():
            score = _score_change(field_name, change)
            if score >= min_score:
                candidates.append(
                    SpotlightEntry(
                        entry_key=diff.key,
                        field=field_name,
                        change=change,
                        reason=_reason_for(field_name, change),
                        score=score,
                    )
                )

    candidates.sort(key=lambda e: e.score, reverse=True)
    return SpotlightResult(
        entries=candidates[:top_n],
        total_scanned=len(diffs),
    )
