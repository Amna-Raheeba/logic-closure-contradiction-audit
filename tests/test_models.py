"""Tests for the data model."""

import pytest

from logic_closure.generate import build_log
from logic_closure.models import (Item, Prediction, PredictionLog,
                                  Relation, RELATION_KINDS)


def test_relation_kinds_are_the_four_declared():
    assert set(RELATION_KINDS) == {"subset", "negation", "exclusion",
                                   "equivalence"}


def test_relation_rejects_unknown_kind():
    with pytest.raises(ValueError):
        Relation("cousins", "a", "b")


def test_item_key_groups_paraphrases():
    first = Item("i1", "e0", "C1", False, "x")
    twin = Item("i2", "e0", "C1", False, "y")
    other = Item("i3", "e0", "C1", True, "z")
    assert first.key() == twin.key()
    assert first.key() != other.key()


def test_log_round_trip_through_dict():
    log, _world = build_log("compact", "typical", 1)
    clone = PredictionLog.from_dict(log.to_dict())
    assert clone.name == log.name
    assert len(clone.items) == len(log.items)
    assert len(clone.relations) == len(log.relations)
    assert clone.planted_noisy == log.planted_noisy
    for item in log.items:
        assert clone.answer(item.item_id) == log.answer(item.item_id)
        assert clone.confidence(item.item_id) \
            == log.confidence(item.item_id)


def test_flipped_log_flips_only_the_named_items():
    log, _world = build_log("compact", "sloppy", 2)
    target = log.items[0].item_id
    other = log.items[1].item_id
    flipped = log.flipped({target})
    assert flipped.answer(target) == (not log.answer(target))
    assert flipped.answer(other) == log.answer(other)
    assert flipped.confidence(target) == log.confidence(target)


def test_prediction_confidence_is_float():
    pred = Prediction(True, 1)
    assert isinstance(pred.confidence, float)
    assert pred.answer is True
