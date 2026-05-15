"""CLI subcommand for differ_bucketizer."""
from __future__ import annotations

import argparse
import json
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_bucketizer import BucketizerError, bucketize


def add_bucketizer_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "bucketize",
        help="Group diff entries into numeric range buckets for a given field.",
    )
    p.add_argument("field", help="Field name whose after-value is used for bucketing.")
    p.add_argument(
        "--boundaries",
        nargs="+",
        type=float,
        required=True,
        metavar="N",
        help="Numeric boundary values that define bucket edges.",
    )
    p.add_argument(
        "--diffs",
        required=True,
        metavar="FILE",
        help="JSON file containing serialised EntryDiff objects.",
    )
    p.set_defaults(func=handle_bucketizer)


def _load_diffs_from_file(path: str) -> List[EntryDiff]:
    with open(path, "r", encoding="utf-8") as fh:
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


def handle_bucketizer(args: argparse.Namespace) -> int:
    try:
        diffs = _load_diffs_from_file(args.diffs)
        result = bucketize(diffs, args.field, args.boundaries)
    except (BucketizerError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"error: {exc}")
        return 1

    print(f"Buckets for field '{result.target_field}' ({result.total_entries} entries matched)")
    for bucket in result.buckets:
        print(f"  {bucket.label:30s}  {bucket.count:>6} entries")
    return 0
