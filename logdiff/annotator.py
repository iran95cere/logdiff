"""Annotator module: attach human-readable notes to field-level changes."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logdiff.differ import EntryDiff, FieldChange


@dataclass
class AnnotatedChange:
    """A FieldChange with an optional annotation note."""

    change: FieldChange
    note: Optional[str] = None

    def __repr__(self) -> str:
        return f"AnnotatedChange(field={self.change.field!r}, note={self.note!r})"


@dataclass
class AnnotatedDiff:
    """An EntryDiff whose changes have been annotated."""

    entry_id: str
    annotated_changes: List[AnnotatedChange] = field(default_factory=list)

    def has_notes(self) -> bool:
        return any(ac.note is not None for ac in self.annotated_changes)


# Built-in annotation rules: (predicate, note) pairs applied in order.
_DEFAULT_RULES: List[tuple] = [
    (lambda fc: fc.field == "status" and fc.before != fc.after, "Status transition detected"),
    (lambda fc: fc.before is None, "New field introduced"),
    (lambda fc: fc.after is None, "Field removed"),
    (lambda fc: isinstance(fc.before, (int, float)) and isinstance(fc.after, (int, float))
                and fc.after > fc.before, "Numeric value increased"),
    (lambda fc: isinstance(fc.before, (int, float)) and isinstance(fc.after, (int, float))
                and fc.after < fc.before, "Numeric value decreased"),
]


def _annotate_change(
    fc: FieldChange,
    custom_rules: Optional[Dict[str, str]] = None,
) -> AnnotatedChange:
    """Return an AnnotatedChange for a single FieldChange.

    custom_rules maps field names to static note strings and takes
    priority over the built-in rule set.
    """
    if custom_rules and fc.field in custom_rules:
        return AnnotatedChange(change=fc, note=custom_rules[fc.field])

    for predicate, note in _DEFAULT_RULES:
        try:
            if predicate(fc):
                return AnnotatedChange(change=fc, note=note)
        except Exception:
            pass

    return AnnotatedChange(change=fc, note=None)


def annotate_diff(
    diff: EntryDiff,
    custom_rules: Optional[Dict[str, str]] = None,
) -> AnnotatedDiff:
    """Annotate all changes in a single EntryDiff."""
    annotated = [
        _annotate_change(fc, custom_rules) for fc in diff.changes
    ]
    return AnnotatedDiff(entry_id=diff.entry_id, annotated_changes=annotated)


def annotate_diffs(
    diffs: List[EntryDiff],
    custom_rules: Optional[Dict[str, str]] = None,
) -> List[AnnotatedDiff]:
    """Annotate a list of EntryDiff objects."""
    return [annotate_diff(d, custom_rules) for d in diffs]
