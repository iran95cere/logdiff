"""CLI sub-commands for managing field aliases."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logdiff.alias import AliasError, AliasRegistry, load_aliases, save_aliases

DEFAULT_ALIAS_FILE = ".logdiff_aliases.json"


def add_alias_args(subparsers: argparse._SubParsersAction) -> None:
    alias_parser = subparsers.add_parser("alias", help="Manage field aliases")
    alias_sub = alias_parser.add_subparsers(dest="alias_cmd", required=True)

    add_p = alias_sub.add_parser("add", help="Add or update an alias")
    add_p.add_argument("name", help="Alias name")
    add_p.add_argument("fields", nargs="+", help="Fields the alias expands to")
    add_p.add_argument("--desc", default=None, help="Optional description")
    add_p.add_argument("--file", default=DEFAULT_ALIAS_FILE, help="Alias file path")

    rm_p = alias_sub.add_parser("remove", help="Remove an alias")
    rm_p.add_argument("name", help="Alias name to remove")
    rm_p.add_argument("--file", default=DEFAULT_ALIAS_FILE, help="Alias file path")

    list_p = alias_sub.add_parser("list", help="List all aliases")
    list_p.add_argument("--file", default=DEFAULT_ALIAS_FILE, help="Alias file path")


def _load_or_empty(path: str) -> AliasRegistry:
    try:
        return load_aliases(path)
    except AliasError:
        return AliasRegistry()


def handle_alias(args: argparse.Namespace) -> int:
    cmd = args.alias_cmd

    if cmd == "add":
        registry = _load_or_empty(args.file)
        try:
            alias = registry.add(args.name, args.fields, description=args.desc)
        except AliasError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        save_aliases(registry, args.file)
        print(f"Saved alias '{alias.name}' -> {alias.fields}")
        return 0

    if cmd == "remove":
        registry = _load_or_empty(args.file)
        try:
            registry.remove(args.name)
        except AliasError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        save_aliases(registry, args.file)
        print(f"Removed alias '{args.name}'.")
        return 0

    if cmd == "list":
        registry = _load_or_empty(args.file)
        aliases = registry.list_all()
        if not aliases:
            print("No aliases defined.")
            return 0
        for alias in aliases:
            desc = f"  # {alias.description}" if alias.description else ""
            print(f"  {alias.name}: {', '.join(alias.fields)}{desc}")
        return 0

    print(f"Unknown alias sub-command: {cmd}", file=sys.stderr)
    return 1
