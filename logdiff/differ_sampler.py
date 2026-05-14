"""Random and deterministic sampling of diff lists for large dataset analysis."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import List, Optional

from logdiff.differ import EntryDiff


class SamplerError(Exception):
    """Raised when sampling parameters are invalid."""


@dataclass
class SampleResult:
    """Result of a sampling operation."""

    diffs: List[EntryDiff]
    total_input: int
    sample_size: int
    seed: Optional[int]

    @property
    def sample_rate(self) -> float:
        if self.total_input == 0:
            return 0.0
        return self.sample_size / self.total_input

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SampleResult(sample_size={self.sample_size}, "
            f"total_input={self.total_input}, "
            f"sample_rate={self.sample_rate:.2%})"
        )


def _entry_hash(diff: EntryDiff) -> str:
    """Compute a stable hash for an EntryDiff based on its key."""
    raw = str(diff.key).encode()
    return hashlib.sha256(raw).hexdigest()


def sample_diffs(
    diffs: List[EntryDiff],
    n: Optional[int] = None,
    fraction: Optional[float] = None,
    seed: Optional[int] = None,
    changed_only: bool = False,
) -> SampleResult:
    """Sample a list of EntryDiff objects.

    Args:
        diffs: Full list of diffs to sample from.
        n: Exact number of entries to return.
        fraction: Fraction of entries to return (0.0 – 1.0).
        seed: Random seed for reproducibility.
        changed_only: If True, only consider diffs that have changes.

    Returns:
        SampleResult containing the sampled diffs and metadata.

    Raises:
        SamplerError: If neither or both of *n* and *fraction* are supplied,
                      or if parameters are out of range.
    """
    if n is None and fraction is None:
        raise SamplerError("Provide either 'n' or 'fraction', not neither.")
    if n is not None and fraction is not None:
        raise SamplerError("Provide either 'n' or 'fraction', not both.")

    pool = [d for d in diffs if d.has_changes()] if changed_only else list(diffs)
    total_input = len(pool)

    if fraction is not None:
        if not (0.0 < fraction <= 1.0):
            raise SamplerError("'fraction' must be in the range (0.0, 1.0].")
        n = max(1, int(total_input * fraction))

    if n < 0:
        raise SamplerError("'n' must be a non-negative integer.")

    n = min(n, total_input)

    rng = random.Random(seed)
    sampled = rng.sample(pool, n) if n <= total_input else pool

    return SampleResult(
        diffs=sampled,
        total_input=total_input,
        sample_size=len(sampled),
        seed=seed,
    )


def deterministic_sample(
    diffs: List[EntryDiff],
    fraction: float,
) -> SampleResult:
    """Sample diffs deterministically using entry key hashes (no randomness).

    Useful for consistent sub-sampling across runs without a fixed seed.
    """
    if not (0.0 < fraction <= 1.0):
        raise SamplerError("'fraction' must be in the range (0.0, 1.0].")

    threshold = int(fraction * (2 ** 16))
    selected = [
        d for d in diffs
        if int(_entry_hash(d)[:4], 16) < threshold
    ]

    return SampleResult(
        diffs=selected,
        total_input=len(diffs),
        sample_size=len(selected),
        seed=None,
    )
