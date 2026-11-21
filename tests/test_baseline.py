"""Tests for the negation-only baseline."""

from logic_closure.baseline import negation_baseline
from logic_closure.generate import build_log
from logic_closure.models import (Item, Prediction, PredictionLog,
                                  Relation)


def _log(answers, relations):
    items = [Item(item_id, "e0", "C0", False, "text")
             for item_id in answers]
    predictions = dict((item_id, Prediction(answer, 0.9))
                       for item_id, answer in answers.items())
    return PredictionLog("hand", items, relations, predictions)


def test_baseline_catches_a_broken_negation_pair():
    log = _log({"a": True, "b": True},
               [Relation("negation", "a", "b")])
    result = negation_baseline(log)
    assert result["violated_pairs"] == {("a", "b")}
    assert result["flagged_items"] == {"a", "b"}


def test_baseline_ignores_subset_breaks():
    log = _log({"a": True, "b": False},
               [Relation("subset", "a", "b")])
    result = negation_baseline(log)
    assert result["violated_pairs"] == set()
    assert result["flagged_items"] == set()


def test_baseline_misses_transitive_contradictions():
    log = _log({"a": True, "b": True, "c": False},
               [Relation("subset", "a", "b"),
                Relation("subset", "b", "c")])
    result = negation_baseline(log)
    assert result["violated_pairs"] == set()


def test_baseline_recall_below_auditor_on_generated_logs():
    from logic_closure.audit import audit_log
    from logic_closure.generate import ground_truth_violated_pairs
    log, world = build_log("standard", "sloppy", 3)
    truth = ground_truth_violated_pairs(world, log)
    baseline = negation_baseline(log)
    audit = audit_log(log)
    baseline_hits = len(baseline["violated_pairs"] & truth)
    audit_hits = len(audit.violated_pairs & truth)
    assert baseline_hits < audit_hits
