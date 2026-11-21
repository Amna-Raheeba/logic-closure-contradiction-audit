"""Tests for the closure auditor on hand-built logs."""

from logic_closure.audit import audit_log, relation_broken
from logic_closure.models import (Item, Prediction, PredictionLog,
                                  Relation)


def _log(answers, relations, confidences=None):
    items = [Item(item_id, "e0", "C0", False, "text %s" % item_id)
             for item_id in answers]
    predictions = {}
    for item_id, answer in answers.items():
        confidence = 0.9
        if confidences and item_id in confidences:
            confidence = confidences[item_id]
        predictions[item_id] = Prediction(answer, confidence)
    return PredictionLog("hand", items, relations, predictions)


def test_direct_negation_violation():
    log = _log({"a": True, "b": True},
               [Relation("negation", "a", "b")])
    audit = audit_log(log)
    assert audit.violated_pairs == {("a", "b")}
    assert audit.direct_count == 1
    assert audit.transitive_count == 0
    assert not audit.consistent


def test_direct_subset_violation():
    log = _log({"a": True, "b": False},
               [Relation("subset", "a", "b")])
    audit = audit_log(log)
    assert audit.violated_pairs == {("a", "b")}
    assert audit.direct_count == 1


def test_direct_exclusion_violation():
    log = _log({"a": True, "b": True},
               [Relation("exclusion", "a", "b")])
    audit = audit_log(log)
    assert audit.violated_pairs == {("a", "b")}


def test_direct_equivalence_violation():
    log = _log({"a": True, "b": False},
               [Relation("equivalence", "a", "b")])
    audit = audit_log(log)
    assert audit.violated_pairs == {("a", "b")}


def test_transitive_chain_violation():
    log = _log({"a": True, "b": True, "c": False},
               [Relation("subset", "a", "b"),
                Relation("subset", "b", "c")])
    audit = audit_log(log)
    assert audit.violated_pairs == {("a", "c"), ("b", "c")}
    assert audit.direct_count == 1
    assert audit.transitive_count == 1
    witness = [v for v in audit.violations if v.pair == ("a", "c")][0]
    assert witness.path_length == 2
    assert witness.witness[0] == ("a", True)
    assert witness.witness[-1] == ("c", True)


def test_consistent_log_has_no_violations():
    log = _log({"a": False, "b": True, "c": True},
               [Relation("subset", "a", "b"),
                Relation("subset", "b", "c")])
    audit = audit_log(log)
    assert audit.consistent
    assert audit.violation_rate == 0.0
    assert audit.weighted_violation_rate == 0.0


def test_unlinked_pairs_are_not_counted():
    log = _log({"a": True, "b": True, "c": False},
               [Relation("subset", "a", "b")])
    audit = audit_log(log)
    assert ("a", "c") not in audit.linked_pairs
    assert ("b", "c") not in audit.linked_pairs
    assert audit.linked_pairs == {("a", "b")}


def test_violation_rate_over_linked_pairs():
    log = _log({"a": True, "b": False},
               [Relation("subset", "a", "b")])
    audit = audit_log(log)
    assert audit.violation_rate == 1.0
    assert audit.weighted_violation_rate == 1.0


def test_weighted_rate_uses_confidences():
    relations = [Relation("subset", "a", "b"),
                 Relation("subset", "c", "d")]
    log = _log({"a": True, "b": False, "c": True, "d": True},
               relations,
               confidences={"a": 0.99, "b": 0.99,
                            "c": 0.51, "d": 0.51})
    audit = audit_log(log)
    # One of two linked pairs violated; the violated pair carries
    # almost all the confidence weight.
    assert audit.violation_rate == 0.5
    assert audit.weighted_violation_rate > 0.7


def test_relation_broken_truth_table():
    subset = Relation("subset", "a", "b")
    log = _log({"a": True, "b": False}, [subset])
    assert relation_broken(subset, log)
    log = _log({"a": False, "b": False}, [subset])
    assert not relation_broken(subset, log)
    negation = Relation("negation", "a", "b")
    log = _log({"a": False, "b": False}, [negation])
    assert relation_broken(negation, log)
    exclusion = Relation("exclusion", "a", "b")
    log = _log({"a": True, "b": False}, [exclusion])
    assert not relation_broken(exclusion, log)
    equivalence = Relation("equivalence", "a", "b")
    log = _log({"a": True, "b": True}, [equivalence])
    assert not relation_broken(equivalence, log)


def test_conflict_graph_collects_violating_items():
    log = _log({"a": True, "b": True, "c": False},
               [Relation("subset", "a", "b"),
                Relation("subset", "b", "c")])
    audit = audit_log(log)
    assert audit.conflict_nodes == ["a", "b", "c"]
    assert set(audit.conflict_edges) == {("a", "c"), ("b", "c")}
