"""Caching layer for diff results to avoid recomputing expensive comparisons."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

CACHE_VERSION = 1
DEFAULT_CACHE_DIR = Path(".logdiff_cache")


class CacheError(Exception):
    """Raised when a cache operation fails."""


@dataclass
class CacheEntry:
    key: str
    created_at: float
    version: int
    payload: dict

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "created_at": self.created_at,
            "version": self.version,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        return cls(
            key=data["key"],
            created_at=data["created_at"],
            version=data["version"],
            payload=data["payload"],
        )


def _cache_key(before_path: str, after_path: str, extra: str = "") -> str:
    """Derive a stable cache key from file paths and optional extra context."""
    before_stat = os.stat(before_path)
    after_stat = os.stat(after_path)
    fingerprint = "|".join([
        before_path, str(before_stat.st_mtime), str(before_stat.st_size),
        after_path, str(after_stat.st_mtime), str(after_stat.st_size),
        extra,
    ])
    return hashlib.sha256(fingerprint.encode()).hexdigest()


def load_cache(key: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Optional[CacheEntry]:
    """Return a cached entry if it exists and matches the current cache version."""
    cache_file = cache_dir / f"{key}.json"
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text())
        entry = CacheEntry.from_dict(data)
        if entry.version != CACHE_VERSION:
            return None
        return entry
    except (KeyError, json.JSONDecodeError) as exc:
        raise CacheError(f"Corrupt cache entry: {cache_file}") from exc


def save_cache(key: str, payload: dict, cache_dir: Path = DEFAULT_CACHE_DIR) -> CacheEntry:
    """Persist a cache entry to disk."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    entry = CacheEntry(key=key, created_at=time.time(), version=CACHE_VERSION, payload=payload)
    cache_file = cache_dir / f"{key}.json"
    cache_file.write_text(json.dumps(entry.to_dict(), indent=2))
    return entry


def clear_cache(cache_dir: Path = DEFAULT_CACHE_DIR) -> int:
    """Delete all cache entries. Returns the number of files removed."""
    if not cache_dir.exists():
        return 0
    removed = 0
    for cache_file in cache_dir.glob("*.json"):
        cache_file.unlink()
        removed += 1
    return removed
