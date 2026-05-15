"""CLI handler for the compare subcommand."""

from __future__ import annotations

import argparse
import json
from typing import List

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_compare import CompareError, compare_diff_sets


def add_compare_args(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'compare' subcommand."""
    parser = subparsers.add_parser(
        "compare",
        help="Compare two diff result files and surface entry-level differences.",
    )
    parser.add_argument("diff_a", help="Path to first diff JSON file.")
    parser.add_argument("diff_b", help="Path to second diff JSON file.")
    parser.add_argument("--label-a", default="A", help="Label for the first diff set.")
    parser.add_argument("--label-b", default="B", help="Label for the second diff set.")
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="Output result as JSON."
    )


def _load_diffs_from_file(path: str) -> List[EntryDiff]:
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    diffs = []
    for item in raw:
        changes = [
            FieldChange(
                field=c["field"],
                before=c.get("before"),
                after=c.get("after"),
                change_type=c["change_type"],
            )
            for c in item.get("changes", [])
        ]
        diffs.append(EntryDiff(key=item["key"], changes=changes))
    return diffs


def handle_compare(args: argparse.Namespace) -> int:
    """Execute the compare subcommand."""
    try:
        diffs_a = _load_diffs_from_file(args.diff_a)
        diffs_b = _load_diffs_from_file(args.diff_b)
        result = compare_diff_sets(diffs_a, diffs_b, label_a=args.label_a, label_b=args.label_b)
    except (CompareError, FileNotFoundError, KeyError) as exc:
        print(f"error: {exc}")
        return 1

    if args.as_json:
        print(json.dumps({
            "label_a": result.label_a,
            "label_b": result.label_b,
            "only_in_a": result.only_in_a,
            "only_in_b": result.only_in_b,
            "in_both": result.in_both,
            "change_delta": result.change_delta,
        }, indent=2))
    else:
        print(f"Comparing {result.label_a!r} vs {result.label_b!r}")
        print(f"  Only in {result.label_a}: {len(result.only_in_a)} entries")
        print(f"  Only in {result.label_b}: {len(result.only_in_b)} entries")
        print(f"  In both:  {len(result.in_both)} entries")
        sign = "+" if result.change_delta >= 0 else ""
        print(f"  Change delta: {sign}{result.change_delta}")
    return 0
