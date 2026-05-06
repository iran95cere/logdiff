"""CLI helpers for pagination flags and paged output rendering."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from logdiff.differ import EntryDiff
from logdiff.formatter import render_diff
from logdiff.pager import PaginationError, iter_pages, paginate


def add_pager_args(parser: argparse.ArgumentParser) -> None:
    """Register pagination-related arguments on an ArgumentParser."""
    group = parser.add_argument_group("pagination")
    group.add_argument(
        "--page",
        type=int,
        default=None,
        metavar="N",
        help="Display only page N of results (1-based).",
    )
    group.add_argument(
        "--page-size",
        type=int,
        default=20,
        metavar="SIZE",
        help="Number of diff entries per page (default: 20).",
    )
    group.add_argument(
        "--all-pages",
        action="store_true",
        help="Iterate and print all pages sequentially.",
    )


def handle_pager(
    diffs: List[EntryDiff],
    args: argparse.Namespace,
    color: bool = True,
) -> int:
    """Render paginated diff output based on parsed CLI args.

    Returns an exit code (0 on success, 1 on error).
    """
    page_size: int = args.page_size
    page_number: Optional[int] = args.page
    all_pages: bool = getattr(args, "all_pages", False)
    changed_only: bool = getattr(args, "changed_only", False)

    try:
        if all_pages:
            for page in iter_pages(diffs, page_size=page_size, changed_only=changed_only):
                _print_page_header(page.page_number, page.total_pages)
                print(render_diff(page.items, color=color))
            return 0

        target = page_number if page_number is not None else 1
        page = paginate(
            diffs,
            page_number=target,
            page_size=page_size,
            changed_only=changed_only,
        )
        _print_page_header(page.page_number, page.total_pages)
        print(render_diff(page.items, color=color))
        return 0

    except PaginationError as exc:
        print(f"logdiff: pagination error: {exc}", file=sys.stderr)
        return 1


def _print_page_header(page_number: int, total_pages: int) -> None:
    separator = "-" * 40
    print(f"{separator}")
    print(f"  Page {page_number} of {total_pages}")
    print(f"{separator}")
