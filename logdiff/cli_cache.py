"""CLI subcommands for managing the logdiff diff cache."""

from __future__ import annotations

import argparse
from pathlib import Path

from logdiff.differ_cache import (
    DEFAULT_CACHE_DIR,
    CacheError,
    _cache_key,
    clear_cache,
    load_cache,
)


def add_cache_args(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'cache' subcommand group."""
    cache_parser = subparsers.add_parser("cache", help="Manage the diff result cache")
    cache_sub = cache_parser.add_subparsers(dest="cache_cmd", required=True)

    # clear
    clear_p = cache_sub.add_parser("clear", help="Remove all cached diff results")
    clear_p.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        help="Path to cache directory (default: .logdiff_cache)",
    )

    # status
    status_p = cache_sub.add_parser("status", help="Show cache info for a pair of log files")
    status_p.add_argument("before", help="Path to the 'before' log file")
    status_p.add_argument("after", help="Path to the 'after' log file")
    status_p.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR))
    status_p.add_argument("--key-extra", default="", help="Extra string mixed into cache key")


def handle_cache(args: argparse.Namespace) -> int:
    """Dispatch cache subcommands. Returns exit code."""
    cache_dir = Path(args.cache_dir)

    if args.cache_cmd == "clear":
        try:
            removed = clear_cache(cache_dir)
            print(f"Removed {removed} cached entry(s) from {cache_dir}")
            return 0
        except OSError as exc:
            print(f"Error clearing cache: {exc}")
            return 1

    if args.cache_cmd == "status":
        try:
            key = _cache_key(args.before, args.after, args.key_extra)
            entry = load_cache(key, cache_dir)
            if entry is None:
                print(f"No cache entry found (key={key[:12]}...)")
                return 0
            import datetime
            ts = datetime.datetime.fromtimestamp(entry.created_at).isoformat()
            print(f"Cache HIT  key={key[:12]}...  created={ts}  version={entry.version}")
            return 0
        except (CacheError, OSError) as exc:
            print(f"Cache error: {exc}")
            return 1

    print(f"Unknown cache subcommand: {args.cache_cmd}")
    return 1
