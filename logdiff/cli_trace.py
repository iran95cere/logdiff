"""CLI integration for the differ_trace module."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_trace import TraceError, build_trace


def add_trace_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "trace",
        help="Trace field changes across multiple diff snapshots.",
    )
    parser.add_argument(
        "snapshots",
        nargs="+",
        metavar="LABEL:FILE",
        help="Snapshot entries in LABEL:FILE format.",
    )
    parser.add_argument(
        "--field",
        dest="field",
        default=None,
        help="Show trace for a specific field only.",
    )
    parser.add_argument(
        "--unstable-only",
        action="store_true",
        default=False,
        help="Only show fields that changed at least once.",
    )
    parser.set_defaults(func=handle_trace)


def _parse_snapshot_arg(arg: str) -> Tuple[str, str]:
    if ":" not in arg:
        raise TraceError(f"Invalid snapshot argument {arg!r}. Expected LABEL:FILE.")
    label, path = arg.split(":", 1)
    return label.strip(), path.strip()


def _load_diffs_from_file(path: str) -> List[EntryDiff]:
    data = json.loads(Path(path).read_text())
    diffs = []
    for item in data:
        changes = [
            FieldChange(
                field=c["field"],
                before=c.get("before"),
                after=c.get("after"),
                change_type=c["change_type"],
            )
            for c in item.get("changes", [])
        ]
        diffs.append(EntryDiff(key=item["key"], changes=changes))
    return diffs


def handle_trace(args: argparse.Namespace) -> int:
    snapshots = []
    for raw in args.snapshots:
        label, path = _parse_snapshot_arg(raw)
        diffs = _load_diffs_from_file(path)
        snapshots.append((label, diffs))

    result = build_trace(snapshots)

    traces = result.traces
    if args.field:
        traces = {k: v for k, v in traces.items() if k == args.field}
    if args.unstable_only:
        traces = {k: v for k, v in traces.items() if not v.is_stable}

    if not traces:
        print("No matching traces found.")
        return 0

    for fname, trace in sorted(traces.items()):
        status = "unstable" if not trace.is_stable else "stable"
        print(f"  {fname}  [{status}]  changes={trace.total_changes}")
        for pt in trace.points:
            print(f"    {pt.label}: {pt.value}")

    return 0
