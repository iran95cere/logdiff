"""CLI integration for diff clustering."""

from __future__ import annotations

import argparse
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_cluster import ClusterError, cluster_diffs, cluster_summary


def add_cluster_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'cluster' subcommand."""
    parser = subparsers.add_parser(
        "cluster",
        help="Group diffs by similarity of changed fields.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        metavar="FLOAT",
        help="Jaccard similarity threshold for clustering (default: 0.5).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Show only the top N largest clusters.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print cluster summary without listing individual entry keys.",
    )


def handle_cluster(args: argparse.Namespace, diffs: List[EntryDiff]) -> int:
    """Execute clustering and print results.

    Returns:
        0 on success, 1 on error.
    """
    try:
        clusters = cluster_diffs(diffs, threshold=args.threshold)
    except ClusterError as exc:
        print(f"[cluster error] {exc}")
        return 1

    clusters_sorted = sorted(clusters, key=lambda c: c.size, reverse=True)
    if args.top is not None:
        clusters_sorted = clusters_sorted[: args.top]

    summary = cluster_summary(clusters_sorted)

    for cluster_id, info in summary.items():
        print(f"Cluster {cluster_id}: {info['size']} entries, fields={info['common_fields']}")
        if not args.summary_only:
            cluster_obj = next(c for c in clusters_sorted if c.cluster_id == cluster_id)
            for diff in cluster_obj.diffs:
                print(f"  - {diff.key}")

    return 0
