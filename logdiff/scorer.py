"""Score diffs by severity/significance of changes."""

from dataclasses import dataclass, field
from typing import List, Dict
from logdiff.differ import EntryDiff, FieldChange

# Weights for different change types
CHANGE_TYPE_WEIGHTS: Dict[str, float] = {
    "modified": 1.0,
    "added": 0.8,
    "removed": 1.2,
    "status_changed": 2.0,
}

# Bonus weight for specific high-priority field names
FIELD_PRIORITY_BONUS: Dict[str, float] = {
    "status": 1.5,
    "error": 1.5,
    "level": 1.2,
    "code": 1.1,
}


@dataclass
class ScoredDiff:
    entry_diff: EntryDiff
    score: float
    breakdown: Dict[str, float] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"ScoredDiff(key={self.entry_diff.key!r}, score={self.score:.2f})"


def _score_change(change: FieldChange) -> float:
    """Compute a numeric score for a single FieldChange."""
    change_type = change.change_type
    base = CHANGE_TYPE_WEIGHTS.get(change_type, 1.0)
    bonus = FIELD_PRIORITY_BONUS.get(change.field, 0.0)
    return base + bonus


def score_diff(entry_diff: EntryDiff) -> ScoredDiff:
    """Score a single EntryDiff based on its field changes."""
    breakdown: Dict[str, float] = {}
    total = 0.0
    for change in entry_diff.changes:
        s = _score_change(change)
        breakdown[change.field] = s
        total += s
    return ScoredDiff(entry_diff=entry_diff, score=round(total, 4), breakdown=breakdown)


def score_diffs(diffs: List[EntryDiff]) -> List[ScoredDiff]:
    """Score a list of EntryDiffs, returning ScoredDiff objects sorted by score descending."""
    scored = [score_diff(d) for d in diffs]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored


def top_n(scored: List[ScoredDiff], n: int) -> List[ScoredDiff]:
    """Return the top-N highest scoring diffs."""
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    return scored[:n]
