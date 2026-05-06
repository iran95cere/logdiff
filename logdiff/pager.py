"""Pagination support for large diff outputs."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from logdiff.differ import EntryDiff


class PaginationError(Exception):
    """Raised when pagination parameters are invalid."""


@dataclass
class Page:
    """A single page of diff results."""

    items: List[EntryDiff]
    page_number: int
    total_pages: int
    total_items: int
    page_size: int

    @property
    def has_next(self) -> bool:
        return self.page_number < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page_number > 1

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0


def paginate(
    diffs: List[EntryDiff],
    page_number: int = 1,
    page_size: int = 20,
    changed_only: bool = False,
) -> Page:
    """Return a single page of diff results.

    Args:
        diffs: Full list of EntryDiff objects.
        page_number: 1-based page index.
        page_size: Number of items per page.
        changed_only: When True, only include entries that have changes.

    Returns:
        A Page instance for the requested page.

    Raises:
        PaginationError: If page_number or page_size are invalid.
    """
    if page_size < 1:
        raise PaginationError(f"page_size must be >= 1, got {page_size}")
    if page_number < 1:
        raise PaginationError(f"page_number must be >= 1, got {page_number}")

    source = [d for d in diffs if d.has_changes()] if changed_only else list(diffs)
    total_items = len(source)
    total_pages = max(1, math.ceil(total_items / page_size))

    if page_number > total_pages:
        raise PaginationError(
            f"page_number {page_number} exceeds total pages {total_pages}"
        )

    start = (page_number - 1) * page_size
    end = start + page_size
    items = source[start:end]

    return Page(
        items=items,
        page_number=page_number,
        total_pages=total_pages,
        total_items=total_items,
        page_size=page_size,
    )


def iter_pages(
    diffs: List[EntryDiff],
    page_size: int = 20,
    changed_only: bool = False,
):
    """Yield successive Page objects over all diffs."""
    if page_size < 1:
        raise PaginationError(f"page_size must be >= 1, got {page_size}")

    source = [d for d in diffs if d.has_changes()] if changed_only else list(diffs)
    total_pages = max(1, math.ceil(len(source) / page_size))

    for page_number in range(1, total_pages + 1):
        yield paginate(source, page_number=page_number, page_size=page_size)
