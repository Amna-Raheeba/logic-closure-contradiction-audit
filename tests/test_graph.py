"""Tests for the implication graph."""

from logic_closure.graph import ImplicationGraph, negate
from logic_closure.models import Item, Relation


def _item(item_id):
    return Item(item_id, "e0", "C0", False, "text %s" % item_id)


def _graph(relations, ids=("a", "b", "c")):
    return ImplicationGraph([_item(i) for i in ids], relations)


def test_negate_flips_the_value():
    assert negate(("a", True)) == ("a", False)
    assert negate(("a", False)) == ("a", True)


def test_subset_edges_include_contrapositive():
    graph = _graph([Relation("subset", "a", "b")])
    assert ("b", True) in graph.reachable(("a", True))
    assert ("a", False) in graph.reachable(("b", False))
    assert ("b", False) not in graph.reachable(("a", True))


def test_negation_edges_both_directions():
    graph = _graph([Relation("negation", "a", "b")])
    assert ("b", False) in graph.reachable(("a", True))
    assert ("a", False) in graph.reachable(("b", True))
    assert ("b", True) in graph.reachable(("a", False))
    assert ("a", True) in graph.reachable(("b", False))


def test_exclusion_edges():
    graph = _graph([Relation("exclusion", "a", "b")])
    assert ("b", False) in graph.reachable(("a", True))
    assert ("a", False) in graph.reachable(("b", True))
    assert ("b", True) not in graph.reachable(("a", True))


def test_equivalence_edges():
    graph = _graph([Relation("equivalence", "a", "b")])
    assert ("b", True) in graph.reachable(("a", True))
    assert ("a", False) in graph.reachable(("b", False))


def test_reachability_is_transitive():
    graph = _graph([Relation("subset", "a", "b"),
                    Relation("subset", "b", "c")])
    reached = graph.reachable(("a", True))
    assert ("b", True) in reached
    assert ("c", True) in reached


def test_shortest_path_witness():
    graph = _graph([Relation("subset", "a", "b"),
                    Relation("subset", "b", "c")])
    path = graph.shortest_path(("a", True), ("c", True))
    assert path == [("a", True), ("b", True), ("c", True)]


def test_shortest_path_unreachable_returns_none():
    graph = _graph([Relation("subset", "a", "b")])
    assert graph.shortest_path(("b", True), ("a", True)) is None


def test_edge_kind_is_recorded():
    graph = _graph([Relation("subset", "a", "b")])
    assert graph.edge_kind(("a", True), ("b", True)) == "subset"
    assert graph.edge_kind(("a", True), ("c", True)) is None
