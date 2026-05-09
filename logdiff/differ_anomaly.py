"""Anomaly detection for diff results — flags statistically unusual field changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from logdiff.differ import EntryDiff, FieldChange


class AnomalyError(Exception):
    """Raised when anomaly detection cannot proceed."""


@dataclass
class FieldAnomaly:
    field_name: str
    change_count: int
    mean: float
    std_dev: float
    z_score: float

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"FieldAnomaly(field={self.field_name!r}, "
            f"z={self.z_score:.2f}, count={self.change_count})"
        )


@dataclass
class AnomalyReport:
    anomalies: List[FieldAnomaly] = field(default_factory=list)
    threshold: float = 2.0

    @property
    def has_anomalies(self) -> bool:
        return bool(self.anomalies)

    @property
    def top_anomaly(self) -> Optional[FieldAnomaly]:
        if not self.anomalies:
            return None
        return max(self.anomalies, key=lambda a: a.z_score)


def _field_change_counts(diffs: List[EntryDiff]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for diff in diffs:
        for change in diff.changes:
            counts[change.field] = counts.get(change.field, 0) + 1
    return counts


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std_dev(values: List[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


def detect_anomalies(
    diffs: List[EntryDiff], threshold: float = 2.0
) -> AnomalyReport:
    """Detect fields whose change frequency is anomalously high."""
    if not diffs:
        raise AnomalyError("Cannot detect anomalies in an empty diff list.")

    counts = _field_change_counts(diffs)
    if not counts:
        return AnomalyReport(threshold=threshold)

    values = [float(v) for v in counts.values()]
    mean = _mean(values)
    std = _std_dev(values, mean)

    anomalies: List[FieldAnomaly] = []
    for fname, count in counts.items():
        z = (count - mean) / std if std > 0 else 0.0
        if z >= threshold:
            anomalies.append(
                FieldAnomaly(
                    field_name=fname,
                    change_count=count,
                    mean=mean,
                    std_dev=std,
                    z_score=z,
                )
            )

    anomalies.sort(key=lambda a: a.z_score, reverse=True)
    return AnomalyReport(anomalies=anomalies, threshold=threshold)
