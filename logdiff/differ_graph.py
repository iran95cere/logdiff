"""Graph-based change relationship analysis for logdiff."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from logdiff.differ import EntryDiff


class GraphError(Exception):
    """Raised when graph construction or traversal fails."""


@dataclass
class FieldNode:
    """Represents a field in the change graph."""

    name: str
    change_count: int = 0
    co_changed_with: Dict[str, int] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"FieldNode(name={self.name!r}, change_count={self.change_count})"


@dataclass
class DiffGraph:
    """Graph of field co-change relationships across diffs."""

    nodes: Dict[str, FieldNode] = field(default_factory=dict)
    total_entries: int = 0

    def most_connected(self, top_n: int = 5) -> List[FieldNode]:
        """Return the top N most co-changed fields."""
        return sorted(
            self.nodes.values(),
            key=lambda n: sum(n.co_changed_with.values()),
            reverse=True,
        )[:top_n]

    def edges(self) -> List[Tuple[str, str, int]]:
        """Return all edges as (field_a, field_b, weight) sorted by weight desc."""
        seen: Set[Tuple[str, str]] = set()
        result: List[Tuple[str, str, int]] = []
        for name, node in self.nodes.items():
            for other, weight in node.co_changed_with.items():
                key = tuple(sorted([name, other]))
                if key not in seen:
                    seen.add(key)  # type: ignore[arg-type]
                    result.append((key[0], key[1], weight))
        return sorted(result, key=lambda e: e[2], reverse=True)


def build_graph(diffs: List[EntryDiff]) -> DiffGraph:
    """Build a co-change graph from a list of EntryDiff objects."""
    if not diffs:
        raise GraphError("Cannot build graph from empty diff list.")

    graph = DiffGraph(total_entries=len(diffs))

    for diff in diffs:
        changed_fields = [c.field for c in diff.changes]
        for fname in changed_fields:
            if fname not in graph.nodes:
                graph.nodes[fname] = FieldNode(name=fname)
            graph.nodes[fname].change_count += 1

        for i, fa in enumerate(changed_fields):
            for fb in changed_fields[i + 1 :]:
                graph.nodes[fa].co_changed_with[fb] = (
                    graph.nodes[fa].co_changed_with.get(fb, 0) + 1
                )
                graph.nodes[fb].co_changed_with[fa] = (
                    graph.nodes[fb].co_changed_with.get(fa, 0) + 1
                )

    return graph
