"""Watchlist module: track specific fields of interest and flag diffs that touch them."""

from dataclasses import dataclass, field
from typing import List, Optional
from logdiff.differ import EntryDiff, FieldChange


class WatchlistError(Exception):
    """Raised when watchlist operations fail."""


@dataclass
class WatchlistMatch:
    """A diff entry that matched one or more watched fields."""

    entry_diff: EntryDiff
    matched_fields: List[str]

    def __repr__(self) -> str:
        return f"WatchlistMatch(key={self.entry_diff.key!r}, matched={self.matched_fields})"


@dataclass
class Watchlist:
    """Holds a set of field names to watch for changes."""

    fields: List[str] = field(default_factory=list)

    def add(self, field_name: str) -> None:
        if not field_name or not isinstance(field_name, str):
            raise WatchlistError(f"Invalid field name: {field_name!r}")
        if field_name not in self.fields:
            self.fields.append(field_name)

    def remove(self, field_name: str) -> None:
        if field_name not in self.fields:
            raise WatchlistError(f"Field {field_name!r} not in watchlist")
        self.fields.remove(field_name)

    def is_empty(self) -> bool:
        return len(self.fields) == 0


def match_watchlist(diffs: List[EntryDiff], watchlist: Watchlist) -> List[WatchlistMatch]:
    """Return diffs that contain changes to any watched field."""
    if watchlist.is_empty():
        raise WatchlistError("Watchlist is empty; no fields to match against")

    watched = set(watchlist.fields)
    matches: List[WatchlistMatch] = []

    for diff in diffs:
        changed_fields = {c.field for c in diff.changes}
        hit = sorted(watched & changed_fields)
        if hit:
            matches.append(WatchlistMatch(entry_diff=diff, matched_fields=hit))

    return matches


def summarize_watchlist_matches(matches: List[WatchlistMatch]) -> dict:
    """Return a summary dict: total matches and per-field hit counts."""
    field_counts: dict = {}
    for match in matches:
        for f in match.matched_fields:
            field_counts[f] = field_counts.get(f, 0) + 1
    return {
        "total_matches": len(matches),
        "field_hits": field_counts,
    }
