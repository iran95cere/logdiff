"""CLI sub-command for computing and comparing diff signatures."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from logdiff.differ import EntryDiff
from logdiff.differ_signature import SignatureError, build_signature, signatures_match


def add_signature_args(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "signature",
        help="Compute a structural signature for a set of diffs.",
    )
    parser.add_argument(
        "--compare",
        metavar="FILE",
        help="Compare signature against a previously saved JSON signature file.",
    )
    parser.add_argument(
        "--save",
        metavar="FILE",
        help="Save the computed signature to a JSON file.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Number of top fields to display (default: 10).",
    )


def _print_signature(sig, top: int, out=sys.stdout) -> None:
    out.write(f"Entries  : {sig.entry_count}\n")
    out.write(f"Changed  : {sig.changed_count}\n")
    out.write(f"Fields   : {len(sig.field_signatures)}\n")
    out.write(f"Fingerprint: {sig.fingerprint}\n")
    out.write("\nTop fields by occurrence:\n")
    ranked = sorted(
        sig.field_signatures.values(),
        key=lambda fs: fs.occurrence_count,
        reverse=True,
    )[:top]
    for fs in ranked:
        types = ", ".join(sorted(fs.change_types))
        out.write(f"  {fs.field:<30} n={fs.occurrence_count}  types=[{types}]\n")


def handle_signature(args: argparse.Namespace, diffs: List[EntryDiff], out=sys.stdout) -> int:
    try:
        sig = build_signature(diffs)
    except SignatureError as exc:
        sys.stderr.write(f"signature error: {exc}\n")
        return 1

    _print_signature(sig, top=args.top, out=out)

    if args.save:
        data = {
            "entry_count": sig.entry_count,
            "changed_count": sig.changed_count,
            "fingerprint": sig.fingerprint,
            "fields": {
                f: {"change_types": sorted(fs.change_types), "occurrence_count": fs.occurrence_count}
                for f, fs in sig.field_signatures.items()
            },
        }
        with open(args.save, "w") as fh:
            json.dump(data, fh, indent=2)
        out.write(f"\nSignature saved to {args.save}\n")

    if args.compare:
        with open(args.compare) as fh:
            stored = json.load(fh)
        if sig.fingerprint == stored.get("fingerprint"):
            out.write("\n[MATCH] Signatures are identical.\n")
        else:
            out.write("\n[DIFF] Signatures differ.\n")
            return 2

    return 0
