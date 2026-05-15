"""Patch generation from diff results — produce minimal JSON patches (RFC 6902-style)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from logdiff.differ import EntryDiff, FieldChange


class PatchError(Exception):
    """Raised when patch generation fails."""


@dataclass
class PatchOp:
    """A single JSON-patch-style operation."""

    op: str  # 'add', 'remove', 'replace'
    path: str
    value: Optional[Any] = None

    def __repr__(self) -> str:
        if self.value is None:
            return f"PatchOp(op={self.op!r}, path={self.path!r})"
        return f"PatchOp(op={self.op!r}, path={self.path!r}, value={self.value!r})"

    def to_dict(self) -> dict:
        d: dict = {"op": self.op, "path": self.path}
        if self.value is not None:
            d["value"] = self.value
        return d


@dataclass
class EntryPatch:
    """All patch operations for a single log entry."""

    key: str
    ops: List[PatchOp] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.ops) == 0

    def to_dict(self) -> dict:
        return {"key": self.key, "ops": [op.to_dict() for op in self.ops]}


def _change_to_op(change: FieldChange) -> PatchOp:
    """Convert a FieldChange into a PatchOp."""
    json_path = f"/{change.field.replace('.', '/')}"
    if change.before is None and change.after is not None:
        return PatchOp(op="add", path=json_path, value=change.after)
    if change.before is not None and change.after is None:
        return PatchOp(op="remove", path=json_path)
    return PatchOp(op="replace", path=json_path, value=change.after)


def build_patch(diff: EntryDiff) -> EntryPatch:
    """Build an EntryPatch from an EntryDiff."""
    ops = [_change_to_op(c) for c in diff.changes]
    return EntryPatch(key=diff.key, ops=ops)


def build_patches(diffs: List[EntryDiff]) -> List[EntryPatch]:
    """Build patches for a list of EntryDiff objects, skipping unchanged entries."""
    if not diffs:
        raise PatchError("No diffs provided to build_patches.")
    return [build_patch(d) for d in diffs if d.has_changes()]
