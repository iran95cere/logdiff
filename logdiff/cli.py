"""Command-line interface for logdiff."""

import argparse
import sys

from logdiff import load_log
from logdiff.differ import diff_entries
from logdiff.filter import filter_by_fields, filter_by_status
from logdiff.formatter import render_diff
from logdiff.reporter import build_report
from logdiff.sorter import sort_diffs, sort_diffs_by_most_changed, SORT_KEYS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logdiff",
        description="Diff structured JSON log files and surface field-level changes.",
    )
    parser.add_argument("before", help="Path to the baseline log file.")
    parser.add_argument("after", help="Path to the changed log file.")
    parser.add_argument(
        "--include-fields",
        nargs="+",
        metavar="FIELD",
        dest="include_fields",
        help="Only report changes for these fields.",
    )
    parser.add_argument(
        "--exclude-fields",
        nargs="+",
        metavar="FIELD",
        dest="exclude_fields",
        help="Exclude these fields from the diff.",
    )
    parser.add_argument(
        "--status",
        nargs="+",
        metavar="STATUS",
        dest="status_filter",
        help="Only show entries with these statuses (added, removed, modified).",
    )
    parser.add_argument(
        "--sort",
        choices=SORT_KEYS,
        default="key",
        help="Sort output entries by this attribute (default: key).",
    )
    parser.add_argument(
        "--sort-desc",
        action="store_true",
        help="Sort in descending order.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Show only the top N most-changed entries (overrides --sort).",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print only the summary report, not individual diffs.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        before = load_log(args.before)
        after = load_log(args.after)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    diffs = diff_entries(before, after)

    if args.include_fields or args.exclude_fields:
        diffs = filter_by_fields(
            diffs,
            include=args.include_fields,
            exclude=args.exclude_fields,
        )

    if args.status_filter:
        diffs = filter_by_status(diffs, statuses=args.status_filter)

    if args.top is not None:
        diffs = sort_diffs_by_most_changed(diffs, top_n=args.top)
    else:
        diffs = sort_diffs(diffs, by=args.sort, reverse=args.sort_desc)

    report = build_report(diffs)

    if not args.summary_only:
        print(render_diff(diffs))

    from logdiff.formatter import format_summary
    print(format_summary(report))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
