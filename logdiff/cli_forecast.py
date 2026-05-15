"""CLI sub-command: forecast — project future field change rates."""

from __future__ import annotations

import argparse
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_forecast import ForecastError, FieldForecast, build_forecast


def add_forecast_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "forecast",
        help="Project future field change rates from historical diff snapshots.",
    )
    p.add_argument(
        "snapshots",
        nargs="+",
        metavar="SNAPSHOT",
        help="Two or more diff JSON files representing successive time periods.",
    )
    p.add_argument(
        "--steps",
        type=int,
        default=3,
        metavar="N",
        help="Number of future steps to forecast (default: 3).",
    )
    p.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Show only the top N fields by absolute trend slope (default: 5).",
    )
    p.add_argument(
        "--min-history",
        type=int,
        default=2,
        dest="min_history",
        help="Minimum snapshot count required for a field to be included (default: 2).",
    )


def _build_histories_from_diffs(
    snapshot_diffs: List[List[EntryDiff]],
) -> dict[str, List[int]]:
    """Count per-field changes in each snapshot and return a history dict."""
    histories: dict[str, List[int]] = {}
    for diffs in snapshot_diffs:
        counts: dict[str, int] = {}
        for d in diffs:
            for change in d.changes:
                counts[change.field] = counts.get(change.field, 0) + 1
        for fname, cnt in counts.items():
            histories.setdefault(fname, []).append(cnt)
        # Backfill fields that had zero changes in this snapshot
        for fname in list(histories):
            if len(histories[fname]) < len(snapshot_diffs):
                while len(histories[fname]) < len(snapshot_diffs):
                    histories[fname].insert(-1, 0)
    return histories


def _print_forecast(forecasts: List[FieldForecast], top: int) -> None:
    shown = forecasts[:top]
    for ff in shown:
        direction = "↑" if ff.is_growing else ("↓" if ff.trend_slope < 0 else "→")
        print(f"  {direction} {ff.field_name}  (slope={ff.trend_slope:+.2f})")
        for pt in ff.points:
            bar = int(pt.predicted_changes)
            print(
                f"      step+{pt.step}: {pt.predicted_changes:.1f} changes "
                f"[conf={pt.confidence:.0%}]"
            )


def handle_forecast(args: argparse.Namespace) -> int:
    import json
    from logdiff.differ import EntryDiff, FieldChange

    snapshot_diffs: List[List[EntryDiff]] = []
    for path in args.snapshots:
        try:
            with open(path) as fh:
                raw = json.load(fh)
            diffs = [
                EntryDiff(
                    key=e["key"],
                    changes=[FieldChange(**c) for c in e.get("changes", [])],
                )
                for e in raw
            ]
            snapshot_diffs.append(diffs)
        except (OSError, KeyError, TypeError) as exc:
            print(f"error: could not load snapshot {path!r}: {exc}")
            return 2

    try:
        histories = _build_histories_from_diffs(snapshot_diffs)
        forecasts = build_forecast(histories, steps=args.steps, min_history=args.min_history)
    except ForecastError as exc:
        print(f"error: {exc}")
        return 1

    if not forecasts:
        print("No fields met the minimum history requirement.")
        return 0

    print(f"Forecast ({args.steps} steps ahead, top {args.top} fields):")
    _print_forecast(forecasts, args.top)
    return 0
