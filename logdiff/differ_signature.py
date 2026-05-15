"""Compute structural signatures for diff sets to detect schema-level shifts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set

from logdiff.differ import EntryDiff


class SignatureError(Exception):
    """Raised when signature computation fails."""


@dataclass
class FieldSignature:
    """Signature data for a single field across all diffs."""

    field: str
    change_types: Set[str] = field(default_factory=set)
    occurrence_count: int = 0

    def __repr__(self) -> str:
        types = ",".join(sorted(self.change_types))
        return f"FieldSignature({self.field!r}, types={{{types}}}, n={self.occurrence_count})"


@dataclass
class DiffSignature:
    """Structural signature summarising a collection of diffs."""

    entry_count: int
    changed_count: int
    field_signatures: Dict[str, FieldSignature]
    fingerprint: str

    def __repr__(self) -> str:
        return (
            f"DiffSignature(entries={self.entry_count}, "
            f"changed={self.changed_count}, "
            f"fields={len(self.field_signatures)}, "
            f"fingerprint={self.fingerprint[:8]!r})"
        )

    @property
    def active_fields(self) -> List[str]:
        """Fields that appear in at least one change."""
        return sorted(self.field_signatures.keys())


def _collect_field_signatures(diffs: List[EntryDiff]) -> Dict[str, FieldSignature]:
    sigs: Dict[str, FieldSignature] = {}
    for diff in diffs:
        for change in diff.changes:
            fs = sigs.setdefault(change.field, FieldSignature(field=change.field))
            fs.change_types.add(change.change_type)
            fs.occurrence_count += 1
    return sigs


def _compute_fingerprint(field_sigs: Dict[str, FieldSignature], changed_count: int) -> str:
    payload = {
        field: sorted(fs.change_types)
        for field, fs in sorted(field_sigs.items())
    }
    raw = json.dumps({"changed": changed_count, "fields": payload}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def build_signature(diffs: List[EntryDiff]) -> DiffSignature:
    """Build a structural signature from a list of EntryDiff objects."""
    if not diffs:
        raise SignatureError("Cannot build signature from empty diff list.")

    changed = [d for d in diffs if d.has_changes()]
    field_sigs = _collect_field_signatures(changed)
    fingerprint = _compute_fingerprint(field_sigs, len(changed))

    return DiffSignature(
        entry_count=len(diffs),
        changed_count=len(changed),
        field_signatures=field_sigs,
        fingerprint=fingerprint,
    )


def signatures_match(a: DiffSignature, b: DiffSignature) -> bool:
    """Return True if two signatures share the same fingerprint."""
    return a.fingerprint == b.fingerprint
