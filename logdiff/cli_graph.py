"""CLI handler for the differ_graph feature."""

from __future__ import annotations

import argparse
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_graph import GraphError, build_graph


def add_graph_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'graph' subcommand."""
    parser = subparsers.add_parser(
        "graph",
        help="Show field co-change relationship graph.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Number of most-connected fields to display (default: 5).",
    )
    parser.add_argument(
        "--edges",
        action="store_true",
        help="Print all co-change edges with weights.",
    )


def handle_graph(args: argparse.Namespace, diffs: List[EntryDiff]) -> int:
    """Handle the 'graph' subcommand. Returns exit code."""
    try:
        graph = build_graph(diffs)
    except GraphError as exc:
        print(f"[graph] Error: {exc}")
        return 1

    if args.edges:
        edges = graph.edges()
        if not edges:
            print("No co-change edges found.")
            return 0
        print(f"{'Field A':<25} {'Field B':<25} {'Weight':>6}")
        print("-" * 58)
        for fa, fb, weight in edges:
            print(f"{fa:<25} {fb:<25} {weight:>6}")
        return 0

    top_nodes = graph.most_connected(top_n=args.top)
    if not top_nodes:
        print("No field changes recorded.")
        return 0

    print(f"Top {args.top} most co-changed fields ({graph.total_entries} entries):")
    print(f"  {'Field':<25} {'Changes':>8} {'Co-change Links':>16}")
    print("  " + "-" * 52)
    for node in top_nodes:
        links = len(node.co_changed_with)
        print(f"  {node.name:<25} {node.change_count:>8} {links:>16}")

    return 0
