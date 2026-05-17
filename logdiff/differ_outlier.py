"""Outlier detection: identify entries whose change count deviates significantly from the mean."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from logdiff.differ import EntryDiff


class OutlierError(Exception):
    """Raised when outlier detection cannot proceed."""


@dataclass
class OutlierResult:
    entry_key: str
    change_count: int
    z_score: float
    diff: EntryDiff

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"OutlierResult(key={self.entry_key!r}, "
            f"changes={self.change_count}, z={self.z_score:.2f})"
        )


@dataclass
class OutlierReport:
    outliers: List[OutlierResult] = field(default_factory=list)
    mean: float = 0.0
    std_dev: float = 0.0
    threshold: float = 2.0

    @property
    def has_outliers(self) -> bool:
        return len(self.outliers) > 0


def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std_dev(values: List[float], mean: Optional[float] = None) -> float:
    if len(values) < 2:
        return 0.0
    m = mean if mean is not None else _mean(values)
    variance = sum((v - m) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def detect_outliers(
    diffs: List[EntryDiff],
    threshold: float = 2.0,
) -> OutlierReport:
    """Return entries whose change count is *threshold* standard deviations above the mean."""
    if not diffs:
        raise OutlierError("Cannot detect outliers in an empty diff list.")

    counts = [float(len(d.changes)) for d in diffs]
    mean = _mean(counts)
    std = _std_dev(counts, mean)

    outliers: List[OutlierResult] = []
    for diff, count in zip(diffs, counts):
        z = (count - mean) / std if std > 0 else 0.0
        if z >= threshold:
            outliers.append(
                OutlierResult(
                    entry_key=diff.key,
                    change_count=int(count),
                    z_score=z,
                    diff=diff,
                )
            )

    outliers.sort(key=lambda r: r.z_score, reverse=True)
    return OutlierReport(outliers=outliers, mean=mean, std_dev=std, threshold=threshold)
