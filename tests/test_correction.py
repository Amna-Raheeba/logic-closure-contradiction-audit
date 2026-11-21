"""Tests for minimal correction sets (minimum vertex cover)."""

import random

from logic_closure.audit import audit_log
from logic_closure.correction import (correction_for_audit,
                                      greedy_vertex_cover,
                                      min_vertex_cover)
from logic_closure.generate import build_log


def test_empty_graph_needs_no_flips():
    cover, exact = min_vertex_cover([], [])
    assert cover == set()
    assert exact


def test_single_edge_cover_size_one():
    cover, exact = min_vertex_cover(["a", "b"], [("a", "b")])
    assert len(cover) == 1
    assert exact


def test_triangle_cover_size_two():
    edges = [("a", "b"), ("b", "c"), ("a", "c")]
    cover, _exact = min_vertex_cover(["a", "b", "c"], edges)
    assert len(cover) == 2


def test_path_cover_is_the_middle():
    edges = [("a", "b"), ("b", "c")]
    cover, _exact = min_vertex_cover(["a", "b", "c"], edges)
    assert cover == {"b"}


def test_star_cover_is_the_centre():
    edges = [("c", "l1"), ("c", "l2"), ("c", "l3")]
    cover, _exact = min_vertex_cover(["c", "l1", "l2", "l3"], edges)
    assert cover == {"c"}


def test_two_disjoint_edges_need_two():
    edges = [("a", "b"), ("c", "d")]
    cover, _exact = min_vertex_cover(["a", "b", "c", "d"], edges)
    assert len(cover) == 2


def test_cover_actually_covers_every_edge():
    rng = random.Random(7)
    for _trial in range(25):
        nodes = ["n%d" % i for i in range(9)]
        edges = set()
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if rng.random() < 0.3:
                    edges.add((nodes[i], nodes[j]))
        cover, exact = min_vertex_cover(nodes, sorted(edges))
        assert exact
        for first, second in edges:
            assert first in cover or second in cover


def test_greedy_never_beats_exact():
    rng = random.Random(11)
    for _trial in range(25):
        nodes = ["n%d" % i for i in range(8)]
        edges = set()
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if rng.random() < 0.35:
                    edges.add((nodes[i], nodes[j]))
        exact_cover, _ = min_vertex_cover(nodes, sorted(edges))
        greedy = greedy_vertex_cover(nodes, sorted(edges))
        assert len(greedy) >= len(exact_cover)
        for first, second in edges:
            assert first in greedy or second in greedy


def test_correction_restores_consistency_on_generated_logs():
    for profile in ("typical", "sloppy", "chain_breaker"):
        log, _world = build_log("compact", profile, 1)
        audit = audit_log(log)
        correction = correction_for_audit(audit)
        repaired = log.flipped(set(correction["items"]))
        assert audit_log(repaired).consistent


def test_correction_for_consistent_log_is_empty():
    log, _world = build_log("compact", "consistent_liar", 0)
    correction = correction_for_audit(audit_log(log))
    assert correction["size"] == 0
    assert correction["items"] == []
