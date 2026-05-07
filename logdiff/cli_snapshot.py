"""CLI integration for snapshot save/compare commands."""

from __future__ import annotations

import argparse
import sys

from logdiff.snapshot import SnapshotError, compare_with_snapshot, save_snapshot


def add_snapshot_args(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register snapshot sub-commands onto an existing subparsers group."""
    snap_parser = subparsers.add_parser(
        "snapshot", help="Save or compare diff snapshots"
    )
    snap_sub = snap_parser.add_subparsers(dest="snapshot_cmd", required=True)

    # snapshot save
    save_p = snap_sub.add_parser("save", help="Save current report as a snapshot")
    save_p.add_argument("--output", required=True, help="Path to write snapshot JSON")

    # snapshot compare
    cmp_p = snap_sub.add_parser("compare", help="Compare report against a snapshot")
    cmp_p.add_argument("--snapshot", required=True, help="Path to snapshot JSON file")
    cmp_p.add_argument(
        "--fail-on-regression",
        action="store_true",
        default=False,
        help="Exit with code 2 if change rate increased",
    )


def handle_snapshot(args: argparse.Namespace, report, printer=print) -> int:
    """Dispatch snapshot sub-commands. Returns an exit code."""
    try:
        if args.snapshot_cmd == "save":
            save_snapshot(report, args.output)
            printer(f"Snapshot saved to {args.output}")
            return 0

        if args.snapshot_cmd == "compare":
            cmp = compare_with_snapshot(report, args.snapshot)
            printer(f"Snapshot : {cmp.snapshot_path}")
            printer(f"Entries  : {cmp.previous_total} -> {cmp.current_total}")
            printer(f"Changed  : {cmp.previous_changed} -> {cmp.current_changed}")
            printer(f"Rate Δ   : {cmp.change_rate_delta:+.4f}")
            if cmp.new_fields:
                printer(f"New fields     : {', '.join(cmp.new_fields)}")
            if cmp.removed_fields:
                printer(f"Removed fields : {', '.join(cmp.removed_fields)}")
            if cmp.regressed:
                printer("⚠  Regression detected: change rate increased.")
                if args.fail_on_regression:
                    return 2
            elif cmp.improved:
                printer("✓  Improvement detected: change rate decreased.")
            return 0
    except SnapshotError as exc:
        printer(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
