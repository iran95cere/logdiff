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


def _print_cluster(cluster_id: int, info: dict, cluster_obj, summary_only: bool) -> None:  # type: ignore[type-arg]
    """Print a single cluster's summary and optionally its member entry keys.

    Args:
        cluster_id: Numeric identifier for the cluster.
        info: Summary dict containing 'size' and 'common_fields'.
        cluster_obj: The Cluster object holding the individual diffs.
        summary_only: When True, skip printing individual entry keys.
    """
    print(f"Cluster {cluster_id}: {info['size']} entries, fields={info['common_fields']}")
    if not summary_only:
        for diff in cluster_obj.diffs:
            print(f"  - {diff.key}")


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

    # Build a lookup so we avoid repeated linear scans inside the loop.
    cluster_by_id = {c.cluster_id: c for c in clusters_sorted}

    for cluster_id, info in summary.items():
        _print_cluster(cluster_id, info, cluster_by_id[cluster_id], args.summary_only)

    return 0
