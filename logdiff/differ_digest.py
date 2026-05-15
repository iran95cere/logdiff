"""Digest module: produce a compact fingerprint summary of a diff set."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import List

from logdiff.differ import EntryDiff


class DigestError(Exception):
    """Raised when digest generation fails."""


@dataclass
class DiffDigest:
    """Compact fingerprint summary of a collection of diffs."""

    entry_count: int
    changed_count: int
    field_count: int
    top_fields: List[str]
    fingerprint: str

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DiffDigest(entries={self.entry_count}, changed={self.changed_count}, "
            f"fields={self.field_count}, fingerprint={self.fingerprint[:8]}...)"
        )


def _collect_field_counts(diffs: List[EntryDiff]) -> dict:
    counts: dict = {}
    for d in diffs:
        for change in d.changes:
            counts[change.field] = counts.get(change.field, 0) + 1
    return counts


def _compute_fingerprint(diffs: List[EntryDiff]) -> str:
    """Deterministic SHA-256 fingerprint over sorted entry keys and change fields."""
    parts = []
    for d in sorted(diffs, key=lambda x: x.key):
        change_sig = sorted(
            f"{c.field}:{c.change_type}:{c.before}:{c.after}" for c in d.changes
        )
        parts.append({"key": d.key, "changes": change_sig})
    raw = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def build_digest(diffs: List[EntryDiff], top_n: int = 5) -> DiffDigest:
    """Build a DiffDigest from a list of EntryDiff objects.

    Args:
        diffs: List of EntryDiff instances.
        top_n: Number of top changed fields to include.

    Returns:
        A DiffDigest summarising the diff set.

    Raises:
        DigestError: If diffs is empty.
    """
    if not diffs:
        raise DigestError("Cannot build digest from an empty diff list.")

    changed = [d for d in diffs if d.has_changes()]
    field_counts = _collect_field_counts(diffs)
    top_fields = [
        f for f, _ in sorted(field_counts.items(), key=lambda x: -x[1])[:top_n]
    ]
    fingerprint = _compute_fingerprint(diffs)

    return DiffDigest(
        entry_count=len(diffs),
        changed_count=len(changed),
        field_count=len(field_counts),
        top_fields=top_fields,
        fingerprint=fingerprint,
    )
