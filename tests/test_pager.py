"""Tests for logdiff.pager."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.pager import Page, PaginationError, iter_pages, paginate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_change(field: str = "status", old="ok", new="error") -> FieldChange:
    return FieldChange(field=field, old_value=old, new_value=new)


def make_diff(key: str, changed: bool = True) -> EntryDiff:
    changes = [make_change()] if changed else []
    return EntryDiff(key=key, before={"id": key}, after={"id": key}, changes=changes)


DIFFS = [make_diff(str(i), changed=(i % 2 == 0)) for i in range(10)]
# keys 0,2,4,6,8 have changes (5 total changed)


# ---------------------------------------------------------------------------
# paginate()
# ---------------------------------------------------------------------------

def test_paginate_returns_first_page():
    page = paginate(DIFFS, page_number=1, page_size=3)
    assert page.page_number == 1
    assert len(page.items) == 3
    assert page.items[0].key == "0"


def test_paginate_last_page_has_remainder():
    page = paginate(DIFFS, page_number=4, page_size=3)
    assert len(page.items) == 1  # 10 items, page 4 has 1


def test_paginate_total_pages():
    page = paginate(DIFFS, page_number=1, page_size=3)
    assert page.total_pages == 4
    assert page.total_items == 10


def test_paginate_has_next_and_previous():
    page = paginate(DIFFS, page_number=2, page_size=3)
    assert page.has_next is True
    assert page.has_previous is True


def test_paginate_first_page_no_previous():
    page = paginate(DIFFS, page_number=1, page_size=5)
    assert page.has_previous is False


def test_paginate_last_page_no_next():
    page = paginate(DIFFS, page_number=2, page_size=5)
    assert page.has_next is False


def test_paginate_changed_only_filters():
    page = paginate(DIFFS, page_number=1, page_size=10, changed_only=True)
    assert page.total_items == 5
    assert all(d.has_changes() for d in page.items)


def test_paginate_empty_list_returns_single_empty_page():
    page = paginate([], page_number=1, page_size=10)
    assert page.total_pages == 1
    assert page.total_items == 0
    assert page.is_empty is True


def test_paginate_invalid_page_size_raises():
    with pytest.raises(PaginationError, match="page_size"):
        paginate(DIFFS, page_number=1, page_size=0)


def test_paginate_invalid_page_number_raises():
    with pytest.raises(PaginationError, match="page_number"):
        paginate(DIFFS, page_number=0, page_size=5)


def test_paginate_page_number_exceeds_total_raises():
    with pytest.raises(PaginationError, match="exceeds total pages"):
        paginate(DIFFS, page_number=99, page_size=5)


# ---------------------------------------------------------------------------
# iter_pages()
# ---------------------------------------------------------------------------

def test_iter_pages_yields_all_pages():
    pages = list(iter_pages(DIFFS, page_size=3))
    assert len(pages) == 4


def test_iter_pages_items_cover_all_diffs():
    pages = list(iter_pages(DIFFS, page_size=4))
    collected = [item for page in pages for item in page.items]
    assert len(collected) == len(DIFFS)


def test_iter_pages_changed_only():
    pages = list(iter_pages(DIFFS, page_size=3, changed_only=True))
    collected = [item for page in pages for item in page.items]
    assert len(collected) == 5


def test_iter_pages_invalid_page_size_raises():
    with pytest.raises(PaginationError):
        list(iter_pages(DIFFS, page_size=-1))
