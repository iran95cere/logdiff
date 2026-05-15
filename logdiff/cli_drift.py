"""CLI sub-command: drift — compare field change rates across two diff snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_drift import detect_drift, DriftError


def add_drift_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "drift",
        help="Detect field-level change-rate drift between two diff snapshots.",
    )
    p.add_argument("before", metavar="BEFORE", help="JSON file with 'before' diffs")
    p.add_argument("after", metavar="AFTER", help="JSON file with 'after' diffs")
    p.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        metavar="T",
        help="Minimum absolute delta to flag as significant (default: 0.05)",
    )
    p.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Show top N drifted fields (default: 10)",
    )
    p.add_argument(
        "--significant-only",
        action="store_true",
        help="Only show fields exceeding the threshold",
    )


def _load_diffs_from_file(path: str) -> List[EntryDiff]:
    with open(path) as fh:
        raw = json.load(fh)
    diffs: List[EntryDiff] = []
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


def handle_drift(args: argparse.Namespace) -> int:
    try:
        before_diffs = _load_diffs_from_file(args.before)
        after_diffs = _load_diffs_from_file(args.after)
        report = detect_drift(before_diffs, after_diffs, threshold=args.threshold)
    except (DriftError, FileNotFoundError, KeyError) as exc:
        print(f"drift: error: {exc}", file=sys.stderr)
        return 1

    fields = report.significant if args.significant_only else report.top(args.top)

    if not fields:
        print("No drift detected.")
        return 0

    print(f"{'Field':<30} {'Before':>8} {'After':>8} {'Delta':>9}")
    print("-" * 60)
    for fd in fields:
        marker = "*" if abs(fd.delta) >= args.threshold else " "
        print(
            f"{fd.field_name:<30} {fd.rate_before:>7.1%} {fd.rate_after:>7.1%}"
            f" {fd.delta:>+8.1%} {marker}"
        )
    return 0
