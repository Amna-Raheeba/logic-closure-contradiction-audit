"""Tests for the seeded generator and the independent oracle."""

from logic_closure.audit import audit_log, relation_broken
from logic_closure.generate import (PROFILES, SCENARIOS, build_items,
                                    build_log, build_world,
                                    ground_truth_violated_pairs,
                                    semantic_implies)
from logic_closure.models import Prediction


def test_scenarios_and_profiles_catalogue():
    assert set(SCENARIOS) == {"compact", "standard"}
    assert set(PROFILES) == {"careful", "typical", "sloppy",
                             "chain_breaker", "consistent_liar"}


def test_generation_is_deterministic():
    first, _ = build_log("standard", "typical", 4)
    second, _ = build_log("standard", "typical", 4)
    assert first.to_dict() == second.to_dict()


def test_different_seeds_differ():
    first, _ = build_log("standard", "typical", 4)
    second, _ = build_log("standard", "typical", 5)
    assert first.to_dict() != second.to_dict()


def test_world_truth_breaks_no_declared_relation():
    for seed in range(3):
        world = build_world("standard", seed)
        items, relations = build_items(world, seed)
        truthful = dict(
            (item.item_id,
             Prediction(world.item_truth(item), 0.9))
            for item in items)
        from logic_closure.models import PredictionLog
        log = PredictionLog("truth", items, relations, truthful)
        for relation in relations:
            assert not relation_broken(relation, log)
        assert audit_log(log).consistent
        assert ground_truth_violated_pairs(world, log) == set()


def test_planted_noisy_matches_world_truth():
    for profile in PROFILES:
        log, world = build_log("compact", profile, 2)
        truth = dict((item.item_id, world.item_truth(item))
                     for item in log.items)
        expected = sorted(item_id for item_id in truth
                          if log.answer(item_id) != truth[item_id])
        assert log.planted_noisy == expected


def test_consistent_liar_is_wrong_but_consistent():
    for seed in range(3):
        log, world = build_log("standard", "consistent_liar", seed)
        assert len(log.planted_noisy) > 0
        assert ground_truth_violated_pairs(world, log) == set()
        assert audit_log(log).consistent


def test_chain_breaker_plants_transitive_violations():
    log, _world = build_log("standard", "chain_breaker", 3)
    audit = audit_log(log)
    assert audit.transitive_count > 0
    assert audit.direct_count > 0


def test_confidences_within_declared_band():
    log, _world = build_log("standard", "sloppy", 0)
    for item in log.items:
        confidence = log.confidence(item.item_id)
        assert 0.51 <= confidence <= 0.99


def test_semantic_implies_membership_propagates_up_only():
    world = build_world("standard", 3)
    items, _relations = build_items(world, 3)
    by_key = dict((item.key(), item) for item in items)
    entity = sorted(world.entity_leaf)[0]
    leaf = world.entity_leaf[entity]
    chain = world.ancestors(leaf)
    if len(chain) < 2:
        return
    child = by_key[(entity, chain[0], False)]
    parent = by_key[(entity, chain[1], False)]
    assert semantic_implies(world, (child, True), (parent, True))
    assert not semantic_implies(world, (parent, True), (child, True))
    assert semantic_implies(world, (parent, False), (child, False))
    assert not semantic_implies(world, (child, False),
                                (parent, False))


def test_semantic_implies_disjoint_excludes():
    world = build_world("standard", 3)
    items, _relations = build_items(world, 3)
    by_key = dict((item.key(), item) for item in items)
    entity = sorted(world.entity_leaf)[0]
    leaf = world.entity_leaf[entity]
    disjoint = [cat for cat in world.parent
                if world.disjoint(cat, leaf)
                and (entity, cat, False) in by_key]
    if not disjoint:
        return
    member_item = by_key[(entity, leaf, False)]
    other_item = by_key[(entity, disjoint[0], False)]
    assert semantic_implies(world, (member_item, True),
                            (other_item, False))
    assert not semantic_implies(world, (member_item, True),
                                (other_item, True))


def test_no_cross_entity_implication():
    world = build_world("standard", 3)
    items, _relations = build_items(world, 3)
    entities = sorted(world.entity_leaf)
    if len(entities) < 2:
        return
    first = [item for item in items
             if item.entity == entities[0]][0]
    second = [item for item in items
              if item.entity == entities[1]][0]
    assert not semantic_implies(world, (first, True), (second, True))
    assert not semantic_implies(world, (first, True), (second, False))
