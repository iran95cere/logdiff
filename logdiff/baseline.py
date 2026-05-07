"""Baseline management: save and load reference snapshots for comparison."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

DEFAULT_BASELINE_DIR = ".logdiff_baselines"


class BaselineError(Exception):
    """Raised when a baseline operation fails."""


@dataclass
class Baseline:
    name: str
    created_at: str
    entries: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "entries": self.entries,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Baseline":
        return cls(
            name=data["name"],
            created_at=data["created_at"],
            entries=data["entries"],
            metadata=data.get("metadata", {}),
        )


def save_baseline(
    name: str,
    entries: list[dict[str, Any]],
    baseline_dir: str = DEFAULT_BASELINE_DIR,
    metadata: dict[str, Any] | None = None,
) -> Baseline:
    """Persist a named baseline snapshot to disk."""
    os.makedirs(baseline_dir, exist_ok=True)
    baseline = Baseline(
        name=name,
        created_at=datetime.now(timezone.utc).isoformat(),
        entries=entries,
        metadata=metadata or {},
    )
    path = _baseline_path(name, baseline_dir)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(baseline.to_dict(), fh, indent=2)
    return baseline


def load_baseline(name: str, baseline_dir: str = DEFAULT_BASELINE_DIR) -> Baseline:
    """Load a previously saved baseline by name."""
    path = _baseline_path(name, baseline_dir)
    if not os.path.exists(path):
        raise BaselineError(f"Baseline '{name}' not found at {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Baseline.from_dict(data)


def list_baselines(baseline_dir: str = DEFAULT_BASELINE_DIR) -> list[str]:
    """Return names of all saved baselines."""
    if not os.path.isdir(baseline_dir):
        return []
    return [
        fname[:-5]
        for fname in os.listdir(baseline_dir)
        if fname.endswith(".json")
    ]


def delete_baseline(name: str, baseline_dir: str = DEFAULT_BASELINE_DIR) -> None:
    """Remove a saved baseline file."""
    path = _baseline_path(name, baseline_dir)
    if not os.path.exists(path):
        raise BaselineError(f"Baseline '{name}' not found at {path}")
    os.remove(path)


def _baseline_path(name: str, baseline_dir: str) -> str:
    safe = name.replace(os.sep, "_")
    return os.path.join(baseline_dir, f"{safe}.json")
