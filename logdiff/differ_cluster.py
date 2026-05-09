"""Cluster diffs by similarity based on shared changed fields."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from logdiff.differ import EntryDiff


class ClusterError(Exception):
    """Raised when clustering fails."""


@dataclass
class DiffCluster:
    cluster_id: int
    diffs: List[EntryDiff] = field(default_factory=list)
    common_fields: Set[str] = field(default_factory=set)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DiffCluster(id={self.cluster_id}, size={len(self.diffs)}, "
            f"fields={sorted(self.common_fields)})"
        )

    @property
    def size(self) -> int:
        return len(self.diffs)


def _changed_fields(diff: EntryDiff) -> Set[str]:
    """Return the set of field names that have changes in an EntryDiff."""
    return {c.field for c in diff.changes}


def _jaccard(a: Set[str], b: Set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def cluster_diffs(
    diffs: List[EntryDiff],
    threshold: float = 0.5,
) -> List[DiffCluster]:
    """Group diffs into clusters based on Jaccard similarity of changed fields.

    Args:
        diffs: List of EntryDiff objects to cluster.
        threshold: Minimum Jaccard similarity to merge into same cluster.

    Returns:
        List of DiffCluster objects.

    Raises:
        ClusterError: If diffs is empty or threshold is out of range.
    """
    if not diffs:
        raise ClusterError("Cannot cluster an empty list of diffs.")
    if not (0.0 <= threshold <= 1.0):
        raise ClusterError(f"Threshold must be between 0.0 and 1.0, got {threshold}.")

    clusters: List[DiffCluster] = []
    field_sets: List[Set[str]] = []

    for diff in diffs:
        fields = _changed_fields(diff)
        matched = False
        for idx, cluster_fields in enumerate(field_sets):
            if _jaccard(fields, cluster_fields) >= threshold:
                clusters[idx].diffs.append(diff)
                clusters[idx].common_fields = cluster_fields & fields
                field_sets[idx] = cluster_fields | fields
                matched = True
                break
        if not matched:
            cluster_id = len(clusters)
            clusters.append(DiffCluster(cluster_id=cluster_id, diffs=[diff], common_fields=set(fields)))
            field_sets.append(set(fields))

    return clusters


def cluster_summary(clusters: List[DiffCluster]) -> Dict[int, Dict]:
    """Return a summary dict keyed by cluster_id."""
    return {
        c.cluster_id: {
            "size": c.size,
            "common_fields": sorted(c.common_fields),
        }
        for c in clusters
    }
