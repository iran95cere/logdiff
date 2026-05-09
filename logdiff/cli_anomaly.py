"""CLI integration for anomaly detection."""

from __future__ import annotations

import argparse
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_anomaly import AnomalyError, detect_anomalies


def add_anomaly_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'anomaly' subcommand."""
    parser = subparsers.add_parser(
        "anomaly",
        help="Detect anomalously changed fields across diff results.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        metavar="Z",
        help="Z-score threshold above which a field is flagged (default: 2.0).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Show only the top N anomalies (default: 5).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print anomalous field names, one per line.",
    )


def handle_anomaly(
    args: argparse.Namespace,
    diffs: List[EntryDiff],
    *,
    print_fn=print,
) -> int:
    """Execute anomaly detection and print results. Returns exit code."""
    try:
        report = detect_anomalies(diffs, threshold=args.threshold)
    except AnomalyError as exc:
        print_fn(f"[anomaly] error: {exc}")
        return 1

    if not report.has_anomalies:
        print_fn("No anomalies detected.")
        return 0

    top_n = report.anomalies[: args.top]

    if args.quiet:
        for anomaly in top_n:
            print_fn(anomaly.field_name)
        return 0

    print_fn(f"Anomalies detected (threshold z>={args.threshold}):\n")
    for anomaly in top_n:
        print_fn(
            f"  {anomaly.field_name:<30}  "
            f"count={anomaly.change_count}  "
            f"z={anomaly.z_score:.2f}  "
            f"(mean={anomaly.mean:.1f}, std={anomaly.std_dev:.1f})"
        )

    return 0
