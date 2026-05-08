"""Template-based rendering for diff reports.

Allows users to define named output templates (e.g. 'slack', 'html', 'brief')
that map to a specific combination of format options and field filters.
"""

from dataclasses import dataclass, field
from typing import Optional
import json
import os

TEMPLATE_FILE = os.path.expanduser("~/.logdiff_templates.json")


class TemplateError(Exception):
    """Raised when a template operation fails."""


@dataclass
class Template:
    name: str
    format: str  # e.g. 'text', 'json', 'csv', 'markdown'
    fields: list[str] = field(default_factory=list)
    exclude_fields: list[str] = field(default_factory=list)
    summary_only: bool = False
    min_score: Optional[float] = None
    description: str = ""

    def __repr__(self) -> str:
        return (
            f"Template(name={self.name!r}, format={self.format!r}, "
            f"summary_only={self.summary_only})"
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "format": self.format,
            "fields": self.fields,
            "exclude_fields": self.exclude_fields,
            "summary_only": self.summary_only,
            "min_score": self.min_score,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Template":
        return cls(
            name=data["name"],
            format=data.get("format", "text"),
            fields=data.get("fields", []),
            exclude_fields=data.get("exclude_fields", []),
            summary_only=data.get("summary_only", False),
            min_score=data.get("min_score"),
            description=data.get("description", ""),
        )


def save_template(template: Template, path: str = TEMPLATE_FILE) -> None:
    """Persist a template to the template store."""
    registry = _load_all(path)
    registry[template.name] = template.to_dict()
    with open(path, "w") as fh:
        json.dump(registry, fh, indent=2)


def load_template(name: str, path: str = TEMPLATE_FILE) -> Template:
    """Load a named template from the store."""
    registry = _load_all(path)
    if name not in registry:
        raise TemplateError(f"Template {name!r} not found.")
    return Template.from_dict(registry[name])


def list_templates(path: str = TEMPLATE_FILE) -> list[Template]:
    """Return all stored templates."""
    return [Template.from_dict(v) for v in _load_all(path).values()]


def remove_template(name: str, path: str = TEMPLATE_FILE) -> None:
    """Delete a named template from the store."""
    registry = _load_all(path)
    if name not in registry:
        raise TemplateError(f"Template {name!r} not found.")
    del registry[name]
    with open(path, "w") as fh:
        json.dump(registry, fh, indent=2)


def _load_all(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return json.load(fh)
