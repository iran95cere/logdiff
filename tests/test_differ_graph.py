"""Tests for logdiff.differ_graph."""

import pytest

from logdiff.differ import EntryDiff, FieldChange
from logdiff.differ_graph import GraphError, build_graph


def make_change(field: str, before=None, after=None) -> FieldChange:
    return FieldChange(field=field, before=before, after=after)


def make_diff(key: str, *fields: str, status: str = "modified") -> EntryDiff:
    changes = [make_change(f, before="old", after="new") for f in fields]
    return EntryDiff(key=key, status=status, changes=changes)


def test_build_graph_empty_raises():
    with pytest.raises(GraphError, match="empty"):
        build_graph([])


def test_build_graph_single_field():
    diffs = [make_diff("e1", "level")]
    graph = build_graph(diffs)
    assert "level" in graph.nodes
    assert graph.nodes["level"].change_count == 1


def test_build_graph_counts_changes_across_entries():
    diffs = [
        make_diff("e1", "level"),
        make_diff("e2", "level"),
        make_diff("e3", "status"),
    ]
    graph = build_graph(diffs)
    assert graph.nodes["level"].change_count == 2
    assert graph.nodes["status"].change_count == 1


def test_build_graph_records_co_changes():
    diffs = [make_diff("e1", "level", "status")]
    graph = build_graph(diffs)
    assert graph.nodes["level"].co_changed_with.get("status") == 1
    assert graph.nodes["status"].co_changed_with.get("level") == 1


def test_build_graph_co_change_weight_accumulates():
    diffs = [
        make_diff("e1", "level", "status"),
        make_diff("e2", "level", "status"),
    ]
    graph = build_graph(diffs)
    assert graph.nodes["level"].co_changed_with["status"] == 2


def test_build_graph_no_self_co_change():
    diffs = [make_diff("e1", "level")]
    graph = build_graph(diffs)
    assert "level" not in graph.nodes["level"].co_changed_with


def test_build_graph_total_entries():
    diffs = [make_diff("e1", "a"), make_diff("e2", "b"), make_diff("e3", "c")]
    graph = build_graph(diffs)
    assert graph.total_entries == 3


def test_most_connected_returns_top_n():
    diffs = [
        make_diff("e1", "a", "b", "c"),
        make_diff("e2", "a", "b"),
        make_diff("e3", "a"),
    ]
    graph = build_graph(diffs)
    top = graph.most_connected(top_n=2)
    assert len(top) == 2
    assert top[0].name == "a"  # most co-changes


def test_edges_returns_unique_pairs():
    diffs = [make_diff("e1", "x", "y")]
    graph = build_graph(diffs)
    edges = graph.edges()
    pairs = [(e[0], e[1]) for e in edges]
    assert len(pairs) == len(set(pairs))


def test_edges_sorted_by_weight_descending():
    diffs = [
        make_diff("e1", "a", "b"),
        make_diff("e2", "a", "b"),
        make_diff("e3", "a", "c"),
    ]
    graph = build_graph(diffs)
    edges = graph.edges()
    weights = [e[2] for e in edges]
    assert weights == sorted(weights, reverse=True)


def test_field_node_repr():
    diffs = [make_diff("e1", "level")]
    graph = build_graph(diffs)
    r = repr(graph.nodes["level"])
    assert "level" in r
    assert "change_count" in r
