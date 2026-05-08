"""Tag diffs with user-defined or auto-generated labels for categorization."""

from dataclasses import dataclass, field
from typing import Optional
from logdiff.differ import EntryDiff, FieldChange


class TaggerError(Exception):
    """Raised when tagging configuration is invalid."""


@dataclass
class TaggedDiff:
    """An EntryDiff decorated with a set of tags."""

    diff: EntryDiff
    tags: list[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TaggedDiff(key={self.diff.key!r}, tags={self.tags!r})"


# Built-in auto-tag rules: (tag_name, predicate(EntryDiff) -> bool)
_AUTO_RULES: list[tuple[str, object]] = [
    ("added", lambda d: d.status == "added"),
    ("removed", lambda d: d.status == "removed"),
    ("modified", lambda d: d.status == "modified"),
    ("high-churn", lambda d: len(d.changes) >= 5),
    ("status-change", lambda d: any(c.field == "status" for c in d.changes)),
]


def _apply_auto_tags(diff: EntryDiff) -> list[str]:
    """Return auto-generated tags for a diff based on built-in rules."""
    return [name for name, pred in _AUTO_RULES if pred(diff)]  # type: ignore[operator]


def tag_diffs(
    diffs: list[EntryDiff],
    extra_tags: Optional[dict[str, list[str]]] = None,
    auto: bool = True,
) -> list[TaggedDiff]:
    """Tag a list of EntryDiff objects.

    Args:
        diffs: The diffs to tag.
        extra_tags: Optional mapping of entry key -> list of custom tags.
        auto: Whether to apply built-in auto-tagging rules.

    Returns:
        List of TaggedDiff instances.
    """
    extra_tags = extra_tags or {}
    result: list[TaggedDiff] = []
    for diff in diffs:
        tags: list[str] = []
        if auto:
            tags.extend(_apply_auto_tags(diff))
        custom = extra_tags.get(diff.key, [])
        for tag in custom:
            if tag not in tags:
                tags.append(tag)
        result.append(TaggedDiff(diff=diff, tags=tags))
    return result


def filter_by_tag(tagged: list[TaggedDiff], tag: str) -> list[TaggedDiff]:
    """Return only TaggedDiff entries that include the given tag."""
    if not tag:
        raise TaggerError("Tag must be a non-empty string.")
    return [t for t in tagged if tag in t.tags]


def all_tags(tagged: list[TaggedDiff]) -> list[str]:
    """Return a sorted, deduplicated list of all tags present across diffs."""
    seen: set[str] = set()
    for t in tagged:
        seen.update(t.tags)
    return sorted(seen)
