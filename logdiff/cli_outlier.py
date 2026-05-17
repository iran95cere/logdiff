"""CLI subcommand: outlier — surface entries with unusually high change counts."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_outlier import OutlierError, detect_outliers


def add_outlier_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "outlier",
        help="Detect entries with an unusually high number of field changes.",
    )
    parser.add_argument(
        "diff_file",
        help="JSON file produced by a previous logdiff run (list of EntryDiff dicts).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="Z-score threshold above which an entry is considered an outlier (default: 2.0).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="Limit output to the top N outliers.",
    )


def _load_diffs_from_file(path: str) -> List[EntryDiff]:
    with open(path) as fh:
        raw = json.load(fh)
    diffs: List[EntryDiff] = []
    for item in raw:
        from logdiff.differ import FieldChange
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


def handle_outlier(args: argparse.Namespace) -> int:
    try:
        diffs = _load_diffs_from_file(args.diff_file)
        report = detect_outliers(diffs, threshold=args.threshold)
    except (OutlierError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    results = report.outliers
    if args.top is not None:
        results = results[: args.top]

    if not results:
        print("No outliers detected.")
        return 0

    print(
        f"Outliers (threshold={report.threshold}, "
        f"mean={report.mean:.2f}, std={report.std_dev:.2f})"
    )
    for r in results:
        print(f"  [{r.entry_key}]  changes={r.change_count}  z={r.z_score:.2f}")

    return 0
