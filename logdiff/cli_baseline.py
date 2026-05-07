"""CLI sub-commands for baseline management."""

from __future__ import annotations

import argparse
import sys

from logdiff.baseline import (
    BaselineError,
    DEFAULT_BASELINE_DIR,
    delete_baseline,
    list_baselines,
    load_baseline,
    save_baseline,
)
from logdiff.parser import parse_log_file


def add_baseline_args(parser: argparse.ArgumentParser) -> None:
    """Register the --baseline-* flags and sub-commands."""
    sub = parser.add_subparsers(dest="baseline_cmd")

    save_p = sub.add_parser("save", help="Save a baseline snapshot")
    save_p.add_argument("name", help="Baseline label")
    save_p.add_argument("file", help="JSON log file to snapshot")
    save_p.add_argument(
        "--baseline-dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir"
    )

    load_p = sub.add_parser("show", help="Print a saved baseline")
    load_p.add_argument("name", help="Baseline label")
    load_p.add_argument(
        "--baseline-dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir"
    )

    list_p = sub.add_parser("list", help="List all saved baselines")
    list_p.add_argument(
        "--baseline-dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir"
    )

    del_p = sub.add_parser("delete", help="Delete a saved baseline")
    del_p.add_argument("name", help="Baseline label")
    del_p.add_argument(
        "--baseline-dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir"
    )


def handle_baseline(args: argparse.Namespace) -> int:
    """Dispatch baseline sub-commands; return exit code."""
    try:
        if args.baseline_cmd == "save":
            entries = parse_log_file(args.file)
            bl = save_baseline(args.name, entries, baseline_dir=args.baseline_dir)
            print(f"Saved baseline '{bl.name}' ({len(bl.entries)} entries) "
                  f"created at {bl.created_at}")

        elif args.baseline_cmd == "show":
            bl = load_baseline(args.name, baseline_dir=args.baseline_dir)
            print(f"Baseline: {bl.name}  created: {bl.created_at}")
            for entry in bl.entries:
                print(entry)

        elif args.baseline_cmd == "list":
            names = list_baselines(baseline_dir=args.baseline_dir)
            if not names:
                print("No baselines saved.")
            else:
                for name in sorted(names):
                    print(name)

        elif args.baseline_cmd == "delete":
            delete_baseline(args.name, baseline_dir=args.baseline_dir)
            print(f"Deleted baseline '{args.name}'.")

        else:
            print("No baseline sub-command given. Use save/show/list/delete.",
                  file=sys.stderr)
            return 2

    except BaselineError as exc:
        print(f"baseline error: {exc}", file=sys.stderr)
        return 1

    return 0
