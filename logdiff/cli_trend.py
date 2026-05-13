"""CLI integration for differ_trend: trend analysis subcommand."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List

from logdiff.differ_trend import build_trend, TrendError


def add_trend_args(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'trend' subcommand."""
    parser = subparsers.add_parser(
        "trend",
        help="Analyse change-rate trends across multiple diff snapshots.",
    )
    parser.add_argument(
        "snapshots",
        nargs="+",
        metavar="LABEL:FILE",
        help="Snapshot entries in LABEL:FILE format.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Number of most volatile fields to display (default: 5).",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output trend data as JSON.",
    )


def _parse_snapshot_entries(raw: List[str]) -> List[Dict[str, Any]]:
    """Parse LABEL:FILE arguments into snapshot dicts."""
    from logdiff.differ import EntryDiff  # local import to avoid cycles

    snapshots = []
    for entry in raw:
        if ":" not in entry:
            raise TrendError(f"Invalid snapshot argument {entry!r}. Expected LABEL:FILE.")
        label, path = entry.split(":", 1)
        with open(path) as fh:
            data = json.load(fh)
        diffs = [EntryDiff(**d) if isinstance(d, dict) else d for d in data]
        snapshots.append({"label": label, "diffs": diffs})
    return snapshots


def handle_trend(args: argparse.Namespace) -> None:
    """Execute the trend subcommand."""
    try:
        snapshots = _parse_snapshot_entries(args.snapshots)
        trend = build_trend(snapshots)
    except TrendError as exc:
        print(f"[trend error] {exc}")
        return

    if args.output_json:
        output = {
            "avg_change_rate": round(trend.avg_change_rate, 4),
            "points": [
                {
                    "label": p.label,
                    "total_entries": p.total_entries,
                    "changed_entries": p.changed_entries,
                    "change_rate": round(p.change_rate, 4),
                }
                for p in trend.points
            ],
            "volatile_fields": [
                {"field": ft.field, "total_changes": ft.total, "counts": ft.counts}
                for ft in trend.most_volatile_fields(args.top)
            ],
        }
        print(json.dumps(output, indent=2))
        return

    print(f"Trend Analysis  (avg change rate: {trend.avg_change_rate:.1%})")
    print("-" * 50)
    for p in trend.points:
        bar = "#" * int(p.change_rate * 20)
        print(f"  {p.label:<20} {p.change_rate:>6.1%}  |{bar}")

    print(f"\nTop {args.top} volatile fields:")
    for ft in trend.most_volatile_fields(args.top):
        direction = "↑" if ft.is_growing else ("↓" if ft.is_shrinking else "→")
        print(f"  {direction} {ft.field:<30} total={ft.total}")
