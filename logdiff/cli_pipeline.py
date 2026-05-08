"""CLI integration for the diff pipeline with unified flags."""

import argparse
import json
import sys
from typing import List

from logdiff.differ_pipeline import PipelineConfig, PipelineResult, run_pipeline
from logdiff.formatter import render_diff
from logdiff.reporter import DiffReport


def add_pipeline_args(parser: argparse.ArgumentParser) -> None:
    """Register pipeline flags on an existing argument parser."""
    parser.add_argument("--key", default="id", help="Field used to match log entries (default: id)")
    parser.add_argument(
        "--include-fields",
        nargs="+",
        metavar="FIELD",
        help="Only include diffs for these fields",
    )
    parser.add_argument(
        "--exclude-fields",
        nargs="+",
        metavar="FIELD",
        help="Exclude diffs for these fields",
    )
    parser.add_argument("--status", metavar="STATUS", help="Filter entries by change status")
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        metavar="SCORE",
        help="Only show entries with a diff score >= SCORE",
    )
    parser.add_argument("--no-annotate", action="store_true", help="Skip annotation step")
    parser.add_argument("--no-tag", action="store_true", help="Skip tagging step")
    parser.add_argument(
        "--pipeline-json",
        action="store_true",
        help="Output full pipeline result as JSON instead of formatted text",
    )


def handle_pipeline(
    args: argparse.Namespace,
    before: List[dict],
    after: List[dict],
) -> int:
    """Execute the pipeline and print results; returns exit code."""
    config = PipelineConfig(
        include_fields=getattr(args, "include_fields", None),
        exclude_fields=getattr(args, "exclude_fields", None),
        status_filter=getattr(args, "status", None),
        min_score=getattr(args, "min_score", 0.0),
        annotate=not getattr(args, "no_annotate", False),
        tag=not getattr(args, "no_tag", False),
    )

    result: PipelineResult = run_pipeline(before, after, key=args.key, config=config)

    if getattr(args, "pipeline_json", False):
        payload = {
            "total": result.total,
            "changed": result.changed,
            "change_rate": result.report.change_rate,
            "most_changed_fields": result.report.most_changed_fields,
            "diffs": [
                {
                    "key": d.key,
                    "status": d.status,
                    "changes": [
                        {"field": c.field, "before": c.before, "after": c.after}
                        for c in d.changes
                    ],
                }
                for d in result.diffs
            ],
        }
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        output = render_diff(result.diffs)
        sys.stdout.write(output)

    return 0 if result.changed > 0 else 0
