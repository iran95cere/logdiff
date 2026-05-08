"""CLI integration for the tagger module."""

from __future__ import annotations

import argparse
import json
from typing import Optional

from logdiff.tagger import tag_diffs, filter_by_tag, all_tags, TaggerError
from logdiff.differ import EntryDiff


def add_tagger_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'tag' subcommand and its arguments."""
    parser = subparsers.add_parser(
        "tag",
        help="Tag diff entries with auto or custom labels.",
    )
    parser.add_argument(
        "--filter-tag",
        metavar="TAG",
        default=None,
        help="Only show entries that carry this tag.",
    )
    parser.add_argument(
        "--list-tags",
        action="store_true",
        default=False,
        help="Print all distinct tags found and exit.",
    )
    parser.add_argument(
        "--no-auto",
        action="store_true",
        default=False,
        help="Disable built-in auto-tagging rules.",
    )
    parser.add_argument(
        "--extra-tags",
        metavar="JSON",
        default=None,
        help='JSON object mapping entry keys to tag lists, e.g. \'{"req-1": ["p1"]}\'\'.',
    )


def handle_tagger(
    args: argparse.Namespace,
    diffs: list[EntryDiff],
    *,
    output=None,
) -> list:  # returns list[TaggedDiff]
    """Execute the tagger command and print results.

    Args:
        args: Parsed CLI arguments (must include tagger flags).
        diffs: EntryDiff list produced by the core diff pipeline.
        output: Optional writable stream; defaults to stdout.

    Returns:
        The final list of TaggedDiff objects after filtering.
    """
    import sys

    out = output or sys.stdout

    extra_tags: Optional[dict[str, list[str]]] = None
    if args.extra_tags:
        try:
            extra_tags = json.loads(args.extra_tags)
        except json.JSONDecodeError as exc:
            raise TaggerError(f"--extra-tags is not valid JSON: {exc}") from exc

    tagged = tag_diffs(diffs, extra_tags=extra_tags, auto=not args.no_auto)

    if args.list_tags:
        for tag in all_tags(tagged):
            print(tag, file=out)
        return tagged

    if args.filter_tag:
        tagged = filter_by_tag(tagged, args.filter_tag)

    for item in tagged:
        tag_str = ", ".join(item.tags) if item.tags else "(none)"
        print(f"{item.diff.key}  [{tag_str}]", file=out)

    return tagged
