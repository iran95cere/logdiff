"""CLI integration for the timeline feature."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from logdiff.differ_timeline import TimelineError, build_timeline
from logdiff.differ import EntryDiff, diff_entries
from logdiff.__init__ import load_log


def add_timeline_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'timeline' subcommand."""
    p = subparsers.add_parser(
        "timeline",
        help="Compare multiple log snapshots across time and show change trends.",
    )
    p.add_argument(
        "--snapshots",
        nargs="+",
        metavar="LABEL:FILE",
        required=True,
        help="One or more label:filepath pairs, e.g. v1:/logs/v1.json v2:/logs/v2.json",
    )
    p.add_argument(
        "--key",
        default="id",
        help="Field used to match log entries across snapshots (default: id).",
    )
    p.add_argument(
        "--peak",
        action="store_true",
        help="Print only the snapshot with the highest number of changes.",
    )


def _parse_snapshot_arg(token: str) -> tuple[str, str]:
    """Parse 'label:filepath' into (label, filepath)."""
    if ":" not in token:
        raise ValueError(f"Expected LABEL:FILE format, got: {token!r}")
    label, _, path = token.partition(":")
    return label.strip(), path.strip()


def handle_timeline(args: argparse.Namespace) -> None:
    """Execute the timeline subcommand."""
    labeled_diffs = {}

    parsed = [_parse_snapshot_arg(t) for t in args.snapshots]

    # We need at least two snapshots to diff; use consecutive pairs.
    if len(parsed) < 2:
        print("[timeline] At least two snapshots are required.")
        return

    for i in range(len(parsed) - 1):
        before_label, before_path = parsed[i]
        after_label, after_path = parsed[i + 1]
        label = f"{before_label}->{after_label}"
        try:
            before = load_log(before_path)
            after = load_log(after_path)
        except Exception as exc:
            print(f"[timeline] Failed to load files for {label}: {exc}")
            return
        diffs = diff_entries(before, after, key=args.key)
        labeled_diffs[label] = diffs

    try:
        timeline = build_timeline(labeled_diffs)
    except TimelineError as exc:
        print(f"[timeline] Error: {exc}")
        return

    if args.peak:
        peak = timeline.peak_slice()
        if peak:
            print(f"Peak: {peak.label} — {peak.change_count} change(s) across {peak.entry_count} entries")
        return

    for s in timeline.slices:
        print(f"  {s.label}: {s.change_count}/{s.entry_count} entries changed")
