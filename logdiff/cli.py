"""Command-line interface for logdiff."""

import argparse
import sys
from pathlib import Path

from logdiff import load_log
from logdiff.differ import diff_logs
from logdiff.formatter import render_diff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logdiff",
        description="Diff structured JSON log files and surface field-level changes.",
    )
    parser.add_argument("before", type=Path, help="Path to the baseline log file.")
    parser.add_argument("after", type=Path, help="Path to the new log file.")
    parser.add_argument(
        "--key",
        default="id",
        metavar="FIELD",
        help="Field name used to correlate log entries (default: id).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the summary line, not individual diffs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        before_entries = load_log(args.before)
        after_entries = load_log(args.after)
    except Exception as exc:  # noqa: BLE001
        print(f"logdiff: error loading files: {exc}", file=sys.stderr)
        return 1

    diffs = diff_logs(before_entries, after_entries, key=args.key)

    output = render_diff(
        diffs,
        use_color=not args.no_color,
        summary_only=args.summary_only,
    )
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
