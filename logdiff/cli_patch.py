"""CLI integration for patch generation."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_patch import PatchError, build_patches


def add_patch_args(subparsers) -> None:
    """Register the 'patch' subcommand."""
    parser: ArgumentParser = subparsers.add_parser(
        "patch",
        help="Generate JSON patch operations from diff results.",
    )
    parser.add_argument(
        "--key",
        metavar="KEY",
        default=None,
        help="Only emit patch for the entry with this key.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--no-empty",
        action="store_true",
        default=False,
        help="Skip entries with no patch operations.",
    )


def handle_patch(args: Namespace, diffs: List[EntryDiff]) -> int:
    """Handle the 'patch' subcommand."""
    try:
        patches = build_patches(diffs)
    except PatchError as exc:
        print(f"patch error: {exc}", file=sys.stderr)
        return 1

    if args.key:
        patches = [p for p in patches if p.key == args.key]

    if args.no_empty:
        patches = [p for p in patches if not p.is_empty()]

    if not patches:
        print("No patches to display.", file=sys.stderr)
        return 0

    if args.format == "json":
        print(json.dumps([p.to_dict() for p in patches], indent=2))
    else:
        for patch in patches:
            print(f"[{patch.key}]")
            for op in patch.ops:
                value_str = f" -> {op.value!r}" if op.value is not None else ""
                print(f"  {op.op:8s}  {op.path}{value_str}")

    return 0
