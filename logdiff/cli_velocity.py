"""CLI subcommand for differ_velocity: show field change velocity across snapshots."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_velocity import VelocityError, build_velocity


def add_velocity_args(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "velocity",
        help="Show field change velocity across ordered diff snapshots.",
    )
    parser.add_argument(
        "snapshots",
        nargs="+",
        metavar="LABEL:FILE",
        help="Ordered snapshots in LABEL:FILE format.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Number of top fields to display (default: 10).",
    )
    parser.add_argument(
        "--accelerating-only",
        action="store_true",
        help="Show only fields that are accelerating.",
    )


def _parse_snapshot_arg(arg: str) -> Tuple[str, str]:
    if ":" not in arg:
        raise VelocityError(f"Snapshot argument must be LABEL:FILE, got: {arg!r}")
    label, path = arg.split(":", 1)
    return label.strip(), path.strip()


def _load_diffs_from_file(path: str) -> List[EntryDiff]:
    data = json.loads(Path(path).read_text())
    diffs = []
    for item in data:
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


def handle_velocity(args: argparse.Namespace) -> int:
    try:
        snapshot_diffs = []
        for raw in args.snapshots:
            label, fpath = _parse_snapshot_arg(raw)
            diffs = _load_diffs_from_file(fpath)
            snapshot_diffs.append((label, diffs))

        report = build_velocity(snapshot_diffs, top=args.top)
    except (VelocityError, OSError) as exc:
        print(f"error: {exc}")
        return 1

    print(f"Snapshots: {', '.join(report.snapshots)}")
    print()

    fields = report.field_velocities
    if args.accelerating_only:
        fields = [fv for fv in fields if fv.is_accelerating]

    if not fields:
        print("No fields match the given criteria.")
        return 0

    header = f"{'Field':<30} {'Avg':>6}  {'Peak':>5}  Accel?  Counts"
    print(header)
    print("-" * len(header))
    for fv in fields:
        accel = "yes" if fv.is_accelerating else "no"
        counts_str = "  ".join(str(c) for c in fv.counts)
        print(f"{fv.field_name:<30} {fv.average:>6.2f}  {fv.peak:>5}  {accel:<6}  {counts_str}")

    return 0
