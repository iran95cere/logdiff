"""Fuzzy entry matching for diff alignment across log files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class MatcherError(Exception):
    """Raised when matching configuration is invalid."""


@dataclass
class MatchedPair:
    """A matched pair of log entries from before/after."""

    key: str
    before: dict[str, Any]
    after: dict[str, Any]
    score: float  # 0.0–1.0 similarity score

    def __repr__(self) -> str:
        return f"MatchedPair(key={self.key!r}, score={self.score:.2f})"


@dataclass
class MatchResult:
    """Result of matching two sets of log entries."""

    matched: list[MatchedPair] = field(default_factory=list)
    unmatched_before: list[dict[str, Any]] = field(default_factory=list)
    unmatched_after: list[dict[str, Any]] = field(default_factory=list)

    @property
    def match_rate(self) -> float:
        total = len(self.matched) + len(self.unmatched_before) + len(self.unmatched_after)
        return len(self.matched) / total if total > 0 else 0.0


def _entry_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    """Compute a simple field-overlap similarity score between two entries."""
    all_keys = set(a) | set(b)
    if not all_keys:
        return 0.0
    matching = sum(1 for k in all_keys if a.get(k) == b.get(k))
    return matching / len(all_keys)


def match_entries(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    key_field: str = "id",
    fuzzy: bool = False,
    threshold: float = 0.5,
) -> MatchResult:
    """Match entries from before and after lists by key_field or fuzzy similarity."""
    if not 0.0 <= threshold <= 1.0:
        raise MatcherError(f"threshold must be between 0.0 and 1.0, got {threshold}")

    result = MatchResult()
    after_index: dict[Any, dict[str, Any]] = {e.get(key_field): e for e in after if key_field in e}
    matched_after_keys: set[Any] = set()

    for entry in before:
        entry_key = entry.get(key_field)
        if entry_key is not None and entry_key in after_index:
            after_entry = after_index[entry_key]
            score = _entry_similarity(entry, after_entry)
            result.matched.append(MatchedPair(key=str(entry_key), before=entry, after=after_entry, score=score))
            matched_after_keys.add(entry_key)
        elif fuzzy:
            best_score = -1.0
            best_match: dict[str, Any] | None = None
            best_key: Any = None
            for akey, aentry in after_index.items():
                if akey in matched_after_keys:
                    continue
                sim = _entry_similarity(entry, aentry)
                if sim > best_score:
                    best_score = sim
                    best_match = aentry
                    best_key = akey
            if best_match is not None and best_score >= threshold:
                result.matched.append(MatchedPair(key=str(best_key), before=entry, after=best_match, score=best_score))
                matched_after_keys.add(best_key)
            else:
                result.unmatched_before.append(entry)
        else:
            result.unmatched_before.append(entry)

    for entry in after:
        if entry.get(key_field) not in matched_after_keys:
            result.unmatched_after.append(entry)

    return result
