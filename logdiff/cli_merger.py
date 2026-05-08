"""CLI integration for the diff merger feature."""

import argparse
import json
from typing import List

from logdiff.differ import EntryDiff
from logdiff.merger import MergeResult, MergerError, merge_diffs
from logdiff.formatter import render_diff


def add_merger_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'merge' subcommand."""
    parser = subparsers.add_parser(
        "merge",
        help="Merge multiple diff result files into a unified output.",
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="FILE",
        help="Two or more JSON diff result files to merge.",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        metavar="LABEL",
        help="Optional labels for each input (must match count of inputs).",
    )
    parser.add_argument(
        "--prefer-first",
        action="store_true",
        default=False,
        help="Keep values from the first source on conflict (default: prefer last).",
    )
    parser.add_argument(
        "--show-conflicts",
        action="store_true",
        default=False,
        help="Print a summary of conflicting keys after merging.",
    )


def _load_diffs_from_file(path: str) -> List[EntryDiff]:
    """Load a list of EntryDiff objects from a JSON export file."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    diffs = []
    for item in raw:
        changes = [
            __import__("logdiff.differ", fromlist=["FieldChange"]).FieldChange(**c)
            for c in item.get("changes", [])
        ]
        diffs.append(
            EntryDiff(
                before=item.get("before"),
                after=item.get("after"),
                changes=changes,
            )
        )
    return diffs


def handle_merger(args: argparse.Namespace) -> int:
    """Execute the merge subcommand."""
    labels = args.labels if args.labels else [f"source_{i}" for i in range(len(args.inputs))]

    if len(labels) != len(args.inputs):
        print("Error: --labels count must match number of input files.")
        return 2

    sources = {}
    for label, path in zip(labels, args.inputs):
        try:
            sources[label] = _load_diffs_from_file(path)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"Error loading '{path}': {exc}")
            return 1

    try:
        result: MergeResult = merge_diffs(sources, prefer_last=not args.prefer_first)
    except MergerError as exc:
        print(f"Merge error: {exc}")
        return 1

    print(render_diff(result.merged))

    if args.show_conflicts and result.conflicts:
        print(f"\nConflicts ({result.conflict_count}):")
        for key, lbls in result.conflicts.items():
            print(f"  {key}: {', '.join(lbls)}")

    return 0
