"""CLI interface for managing output templates."""

import argparse
from logdiff.templater import (
    Template,
    TemplateError,
    save_template,
    load_template,
    list_templates,
    remove_template,
)


def add_templater_args(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'template' subcommand group."""
    parser = subparsers.add_parser("template", help="Manage output templates")
    sub = parser.add_subparsers(dest="template_cmd", required=True)

    # save
    save_p = sub.add_parser("save", help="Save a new template")
    save_p.add_argument("name", help="Template name")
    save_p.add_argument("--format", default="text", choices=["text", "json", "csv", "markdown"])
    save_p.add_argument("--fields", nargs="+", default=[], metavar="FIELD")
    save_p.add_argument("--exclude-fields", nargs="+", default=[], metavar="FIELD")
    save_p.add_argument("--summary-only", action="store_true")
    save_p.add_argument("--min-score", type=float, default=None)
    save_p.add_argument("--description", default="")

    # show
    show_p = sub.add_parser("show", help="Show a template's settings")
    show_p.add_argument("name", help="Template name")

    # list
    sub.add_parser("list", help="List all saved templates")

    # remove
    rm_p = sub.add_parser("remove", help="Delete a template")
    rm_p.add_argument("name", help="Template name")


def _print_template(tmpl: Template) -> None:
    """Print a template's settings in a human-readable format."""
    print(f"Name        : {tmpl.name}")
    print(f"Format      : {tmpl.format}")
    print(f"Fields      : {tmpl.fields or '(all)'}")
    print(f"Exclude     : {tmpl.exclude_fields or '(none)'}")
    print(f"Summary only: {tmpl.summary_only}")
    print(f"Min score   : {tmpl.min_score}")
    print(f"Description : {tmpl.description}")


def handle_templater(args: argparse.Namespace) -> int:
    """Dispatch template subcommands."""
    try:
        if args.template_cmd == "save":
            tmpl = Template(
                name=args.name,
                format=args.format,
                fields=args.fields,
                exclude_fields=args.exclude_fields,
                summary_only=args.summary_only,
                min_score=args.min_score,
                description=args.description,
            )
            save_template(tmpl)
            print(f"Template {args.name!r} saved.")

        elif args.template_cmd == "show":
            tmpl = load_template(args.name)
            _print_template(tmpl)

        elif args.template_cmd == "list":
            templates = list_templates()
            if not templates:
                print("No templates saved.")
            for t in templates:
                desc = f" \u2014 {t.description}" if t.description else ""
                print(f"  {t.name} [{t.format}]{desc}")

        elif args.template_cmd == "remove":
            remove_template(args.name)
            print(f"Template {args.name!r} removed.")

    except TemplateError as exc:
        print(f"Error: {exc}")
        return 1

    return 0
