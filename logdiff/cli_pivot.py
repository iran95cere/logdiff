"""CLI integration for the pivot table feature."""

from __future__ import annotations

import argparse
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_pivot import PivotError, PivotTable, build_pivot


def add_pivot_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'pivot' subcommand."""
    parser = subparsers.add_parser(
        "pivot",
        help="Pivot field-change counts by a chosen field value.",
    )
    parser.add_argument(
        "--by",
        required=True,
        metavar="FIELD",
        help="Field to pivot rows on (e.g. 'service' or 'status').",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Show only the top N fields by total change count (0 = all).",
    )
    parser.add_argument(
        "--sentinel",
        default="<missing>",
        metavar="VALUE",
        help="Placeholder for entries missing the pivot field.",
    )


def _select_fields(table: PivotTable, top: int) -> List[str]:
    """Return field names, optionally limited to the top-N by total changes."""
    all_fields = table.fields
    if top <= 0:
        return all_fields

    totals = {
        f: sum(table.cell(g, f).total for g in table.groups)
        for f in all_fields
    }
    return sorted(all_fields, key=lambda f: totals[f], reverse=True)[:top]


def handle_pivot(args: argparse.Namespace, diffs: List[EntryDiff]) -> None:
    """Execute the pivot subcommand."""
    try:
        table = build_pivot(diffs, pivot_field=args.by, sentinel=args.sentinel)
    except PivotError as exc:
        print(f"pivot error: {exc}")
        return

    fields = _select_fields(table, args.top)
    if not fields:
        print("No field changes found.")
        return

    # Header row
    col_w = 14
    header = f"{'group':<{col_w}}" + "".join(f"{f:<{col_w}}" for f in fields)
    print(header)
    print("-" * len(header))

    for group in table.groups:
        row = f"{group:<{col_w}}"
        for f in fields:
            cell = table.cell(group, f)
            summary = f"+{cell.added}/~{cell.modified}/-{cell.removed}"
            row += f"{summary:<{col_w}}"
        print(row)
