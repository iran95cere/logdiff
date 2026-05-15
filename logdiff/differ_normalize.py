"""Normalize field values across diffs for consistent comparison."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from logdiff.differ import EntryDiff, FieldChange


class NormalizeError(Exception):
    """Raised when normalization configuration is invalid."""


NormalizerFn = Callable[[Any], Any]

_BUILTIN_NORMALIZERS: Dict[str, NormalizerFn] = {
    "lowercase": lambda v: v.lower() if isinstance(v, str) else v,
    "uppercase": lambda v: v.upper() if isinstance(v, str) else v,
    "strip": lambda v: v.strip() if isinstance(v, str) else v,
    "str": lambda v: str(v) if v is not None else v,
    "int": lambda v: int(v) if v is not None else v,
    "float": lambda v: float(v) if v is not None else v,
    "bool": lambda v: bool(v) if v is not None else v,
}


@dataclass
class NormalizeConfig:
    """Maps field names to normalizer names or callables."""

    rules: Dict[str, str] = field(default_factory=dict)
    custom: Dict[str, NormalizerFn] = field(default_factory=dict)

    def get_normalizer(self, field_name: str) -> Optional[NormalizerFn]:
        if field_name in self.custom:
            return self.custom[field_name]
        rule = self.rules.get(field_name)
        if rule is None:
            return None
        if rule not in _BUILTIN_NORMALIZERS:
            raise NormalizeError(
                f"Unknown normalizer '{rule}' for field '{field_name}'. "
                f"Available: {sorted(_BUILTIN_NORMALIZERS)}"
            )
        return _BUILTIN_NORMALIZERS[rule]


def _normalize_change(change: FieldChange, config: NormalizeConfig) -> FieldChange:
    normalizer = config.get_normalizer(change.field)
    if normalizer is None:
        return change
    new_before = normalizer(change.before) if change.before is not None else change.before
    new_after = normalizer(change.after) if change.after is not None else change.after
    return FieldChange(
        field=change.field,
        before=new_before,
        after=new_after,
        change_type=change.change_type,
    )


def normalize_diffs(
    diffs: List[EntryDiff],
    config: NormalizeConfig,
) -> List[EntryDiff]:
    """Return new EntryDiff list with field values normalized per config."""
    if not diffs:
        return []
    result: List[EntryDiff] = []
    for diff in diffs:
        normalized_changes = [_normalize_change(c, config) for c in diff.changes]
        result.append(
            EntryDiff(
                key=diff.key,
                changes=normalized_changes,
            )
        )
    return result
