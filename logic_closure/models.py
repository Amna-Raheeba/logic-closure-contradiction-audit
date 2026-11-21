"""Data model for a recorded prediction log and its logical relations.

A *log* is a set of items (yes/no propositions a model was asked
about), the model's recorded answer and confidence for each item,
and a set of declared logical relations between items.  The auditor
never sees the model -- only this record.

Relations are declared between items and compiled by
:mod:`logic_closure.graph` into an implication graph over literals.
A literal is a pair ``(item_id, value)`` read as "the item's answer
is ``value``".
"""

REL_SUBSET = "subset"            # A yes implies B yes (A is a subset of B)
REL_NEGATION = "negation"        # A and B are negations of each other
REL_EXCLUSION = "exclusion"      # A and B cannot both be yes
REL_EQUIVALENCE = "equivalence"  # A and B must agree

RELATION_KINDS = (REL_SUBSET, REL_NEGATION, REL_EXCLUSION, REL_EQUIVALENCE)


class Item(object):
    """One proposition in a log.

    ``entity`` and ``category`` describe the proposition's subject in
    the generator's world ("entity e3 is in category C5"); ``negated``
    marks the complementary phrasing ("e3 is not in C5").  A
    paraphrase is a separate item with the same entity, category and
    polarity, linked to its twin by an equivalence relation.
    """

    __slots__ = ("item_id", "entity", "category", "negated", "text")

    def __init__(self, item_id, entity, category, negated, text):
        self.item_id = item_id
        self.entity = entity
        self.category = category
        self.negated = bool(negated)
        self.text = text

    def key(self):
        """The proposition key: two items with the same key state the
        same proposition (paraphrases share a key)."""
        return (self.entity, self.category, self.negated)

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "entity": self.entity,
            "category": self.category,
            "negated": self.negated,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["item_id"], data["entity"], data["category"],
                   data["negated"], data["text"])

    def __repr__(self):
        return "Item(%s)" % self.item_id


class Relation(object):
    """A declared logical relation between two items."""

    __slots__ = ("kind", "a", "b")

    def __init__(self, kind, a, b):
        if kind not in RELATION_KINDS:
            raise ValueError("unknown relation kind: %s" % kind)
        self.kind = kind
        self.a = a
        self.b = b

    def to_dict(self):
        return {"kind": self.kind, "a": self.a, "b": self.b}

    @classmethod
    def from_dict(cls, data):
        return cls(data["kind"], data["a"], data["b"])

    def __repr__(self):
        return "Relation(%s, %s, %s)" % (self.kind, self.a, self.b)


class Prediction(object):
    """A model's recorded answer to one item."""

    __slots__ = ("answer", "confidence")

    def __init__(self, answer, confidence):
        self.answer = bool(answer)
        self.confidence = float(confidence)

    def to_dict(self):
        return {"answer": self.answer, "confidence": self.confidence}

    @classmethod
    def from_dict(cls, data):
        return cls(data["answer"], data["confidence"])


class PredictionLog(object):
    """A recorded set of predictions plus the relations between items.

    ``planted_noisy`` is ground truth available only for generated
    logs: the item ids whose recorded answer differs from the world
    truth.  It is never used by the auditor, only by the evaluation
    that scores the auditor.
    """

    __slots__ = ("name", "items", "relations", "predictions",
                 "planted_noisy", "meta")

    def __init__(self, name, items, relations, predictions,
                 planted_noisy=None, meta=None):
        self.name = name
        self.items = list(items)
        self.relations = list(relations)
        self.predictions = dict(predictions)
        self.planted_noisy = list(planted_noisy or [])
        self.meta = dict(meta or {})

    def item_map(self):
        return dict((item.item_id, item) for item in self.items)

    def answer(self, item_id):
        return self.predictions[item_id].answer

    def confidence(self, item_id):
        return self.predictions[item_id].confidence

    def flipped(self, item_ids):
        """A copy of this log with the given items' answers flipped."""
        predictions = {}
        for item_id, pred in self.predictions.items():
            if item_id in item_ids:
                predictions[item_id] = Prediction(not pred.answer,
                                                  pred.confidence)
            else:
                predictions[item_id] = Prediction(pred.answer,
                                                  pred.confidence)
        return PredictionLog(self.name, self.items, self.relations,
                             predictions, self.planted_noisy, self.meta)

    def to_dict(self):
        return {
            "name": self.name,
            "items": [item.to_dict() for item in self.items],
            "relations": [rel.to_dict() for rel in self.relations],
            "predictions": dict(
                (item_id, pred.to_dict())
                for item_id, pred in self.predictions.items()),
            "planted_noisy": list(self.planted_noisy),
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, data):
        items = [Item.from_dict(entry) for entry in data["items"]]
        relations = [Relation.from_dict(entry)
                     for entry in data["relations"]]
        predictions = dict(
            (item_id, Prediction.from_dict(entry))
            for item_id, entry in data["predictions"].items())
        return cls(data["name"], items, relations, predictions,
                   data.get("planted_noisy"), data.get("meta"))
