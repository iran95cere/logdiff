"""CLI integration for the annotator: adds --annotate flag and handles output."""

import argparse
from typing import Dict, List, Optional

from logdiff.annotator import AnnotatedDiff, annotate_diffs
from logdiff.differ import EntryDiff


def add_annotator_args(parser: argparse.ArgumentParser) -> None:
    """Register annotation-related CLI flags onto *parser*."""
    group = parser.add_argument_group("annotation")
    group.add_argument(
        "--annotate",
        action="store_true",
        default=False,
        help="Attach human-readable notes to each field-level change.",
    )
    group.add_argument(
        "--annotate-rule",
        metavar="FIELD=NOTE",
        action="append",
        dest="annotate_rules",
        default=[],
        help=(
            "Custom annotation rule in FIELD=NOTE format. "
            "Can be repeated for multiple fields."
        ),
    )


def _parse_custom_rules(raw_rules: List[str]) -> Dict[str, str]:
    """Parse a list of 'FIELD=NOTE' strings into a dict."""
    rules: Dict[str, str] = {}
    for raw in raw_rules:
        if "=" not in raw:
            raise argparse.ArgumentTypeError(
                f"Invalid --annotate-rule format (expected FIELD=NOTE): {raw!r}"
            )
        field, _, note = raw.partition("=")
        rules[field.strip()] = note.strip()
    return rules


def handle_annotator(
    args: argparse.Namespace,
    diffs: List[EntryDiff],
) -> Optional[List[AnnotatedDiff]]:
    """If --annotate is set, annotate *diffs* and print a summary.

    Returns the list of AnnotatedDiff objects so callers can use them
    further (e.g. in formatters), or None when annotation is disabled.
    """
    if not getattr(args, "annotate", False):
        return None

    custom_rules = _parse_custom_rules(getattr(args, "annotate_rules", []))
    annotated = annotate_diffs(diffs, custom_rules=custom_rules or None)

    noted = sum(1 for ad in annotated if ad.has_notes())
    total = len(annotated)
    print(f"[annotator] {noted}/{total} entries have annotated changes.")

    for ad in annotated:
        for ac in ad.annotated_changes:
            if ac.note:
                print(f"  [{ad.entry_id}] {ac.change.field}: {ac.note}")

    return annotated
