"""Alias management for logdiff — map short names to field paths or filter presets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import os


class AliasError(Exception):
    """Raised when alias operations fail."""


@dataclass
class Alias:
    name: str
    fields: List[str]
    description: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        return f"Alias(name={self.name!r}, fields={self.fields!r})"


@dataclass
class AliasRegistry:
    _aliases: Dict[str, Alias] = field(default_factory=dict)

    def add(self, name: str, fields: List[str], description: Optional[str] = None) -> Alias:
        if not name or not name.strip():
            raise AliasError("Alias name must not be empty.")
        if not fields:
            raise AliasError("Alias must map to at least one field.")
        alias = Alias(name=name.strip(), fields=list(fields), description=description)
        self._aliases[alias.name] = alias
        return alias

    def get(self, name: str) -> Alias:
        try:
            return self._aliases[name]
        except KeyError:
            raise AliasError(f"Alias {name!r} not found.")

    def remove(self, name: str) -> None:
        if name not in self._aliases:
            raise AliasError(f"Alias {name!r} not found.")
        del self._aliases[name]

    def list_all(self) -> List[Alias]:
        return sorted(self._aliases.values(), key=lambda a: a.name)

    def to_dict(self) -> dict:
        return {
            name: {"fields": alias.fields, "description": alias.description}
            for name, alias in self._aliases.items()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AliasRegistry":
        registry = cls()
        for name, entry in data.items():
            registry.add(name, entry["fields"], entry.get("description"))
        return registry


def save_aliases(registry: AliasRegistry, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(registry.to_dict(), fh, indent=2)


def load_aliases(path: str) -> AliasRegistry:
    if not os.path.exists(path):
        raise AliasError(f"Alias file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return AliasRegistry.from_dict(data)


def resolve_fields(names: List[str], registry: AliasRegistry) -> List[str]:
    """Expand alias names to their field lists; pass through plain field names unchanged."""
    resolved: List[str] = []
    for name in names:
        try:
            alias = registry.get(name)
            resolved.extend(alias.fields)
        except AliasError:
            resolved.append(name)
    return resolved
