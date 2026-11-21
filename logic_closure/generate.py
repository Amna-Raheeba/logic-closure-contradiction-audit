"""Seeded generation of prediction logs with planted ground truth.

The generator builds a small world -- a laminar category tree and a
set of entities, each living in exactly one leaf category -- and
derives yes/no propositions ("items") about entity membership.
Because the categories form a tree, any two categories are either
ancestor-related or disjoint, so the semantic implication between
any two item literals is decidable from the tree alone.  That gives
the evaluation an oracle that is *independent* of the auditor's
implication graph: if the graph construction drops an edge (say a
contrapositive), the oracle still knows the implication holds and
the auditor's recall drops.  Detection is measured, not assumed.

Declared relations given to the auditor are the *direct* ones a real
eval harness would record: subset edges to the immediate parent
category only, exclusion between sibling categories only, negation
pairs, and equivalence for paraphrases.  Everything transitive must
be derived by the auditor's closure.

On top of a world's consistent truth, simulated predictors
("profiles") record answers:

- ``careful`` / ``typical`` / ``sloppy`` flip each answer
  independently at a profile error rate;
- ``chain_breaker`` additionally flips the top of a leaf-to-root
  chain while leaving the leaf asserted, planting contradictions
  that are only visible through transitivity;
- ``consistent_liar`` answers from an *alternative* consistent world
  (entities moved to a sibling leaf): many wrong answers, zero
  contradictions -- the audit's structural blind spot, planted on
  purpose and reported as such.
"""

import random

from .models import (Item, Prediction, PredictionLog, Relation,
                     REL_EQUIVALENCE, REL_EXCLUSION, REL_NEGATION,
                     REL_SUBSET)

SCENARIOS = {
    "compact": {"n_categories": 9, "n_entities": 6},
    "standard": {"n_categories": 15, "n_entities": 10},
}

PROFILES = {
    "careful": {"flip_p": 0.02, "confidence": 0.88},
    "typical": {"flip_p": 0.06, "confidence": 0.80},
    "sloppy": {"flip_p": 0.13, "confidence": 0.72},
    "chain_breaker": {"flip_p": 0.01, "confidence": 0.85},
    "consistent_liar": {"flip_p": 0.0, "confidence": 0.85},
}

MAX_DEPTH = 3


class World(object):
    """A category tree plus entity placements, with truth lookup."""

    def __init__(self, parent, entity_leaf):
        self.parent = dict(parent)          # category -> parent or None
        self.entity_leaf = dict(entity_leaf)  # entity -> leaf category

    def ancestors(self, category):
        """The category itself, then its parents up to the root."""
        chain = []
        node = category
        while node is not None:
            chain.append(node)
            node = self.parent[node]
        return chain

    def depth(self, category):
        return len(self.ancestors(category)) - 1

    def is_ancestor(self, maybe_ancestor, category):
        """True when ``maybe_ancestor`` is ``category`` or above it."""
        return maybe_ancestor in self.ancestors(category)

    def disjoint(self, first, second):
        """True when neither category contains the other (laminar)."""
        return not (self.is_ancestor(first, second)
                    or self.is_ancestor(second, first))

    def member(self, entity, category):
        """World truth: is the entity in the category?"""
        return self.is_ancestor(category, self.entity_leaf[entity])

    def item_truth(self, item):
        truth = self.member(item.entity, item.category)
        return (not truth) if item.negated else truth


def build_world(scenario, seed):
    spec = SCENARIOS[scenario]
    rng = random.Random(1000003 * seed + 17)
    parent = {"C0": None}
    categories = ["C0"]
    attempts = 0
    while len(categories) < spec["n_categories"] and attempts < 10000:
        attempts += 1
        candidate_parent = rng.choice(categories)
        if len(_ancestors_of(parent, candidate_parent)) - 1 >= MAX_DEPTH:
            continue
        name = "C%d" % len(categories)
        parent[name] = candidate_parent
        categories.append(name)
    children = _children_map(parent)
    leaves = [cat for cat in categories if not children.get(cat)]
    entity_leaf = {}
    for index in range(spec["n_entities"]):
        entity_leaf["e%d" % index] = rng.choice(leaves)
    return World(parent, entity_leaf)


def _ancestors_of(parent, category):
    chain = []
    node = category
    while node is not None:
        chain.append(node)
        node = parent[node]
    return chain


def _children_map(parent):
    children = {}
    for category, par in parent.items():
        if par is not None:
            children.setdefault(par, []).append(category)
    return children


def _item_text(entity, category, negated):
    if negated:
        return "entity %s is not in category %s" % (entity, category)
    return "entity %s is in category %s" % (entity, category)


def build_items(world, seed):
    """Derive items and declared (direct) relations from a world."""
    rng = random.Random(2000003 * seed + 29)
    children = _children_map(world.parent)
    items = []
    by_key = {}

    def add_item(entity, category, negated):
        key = (entity, category, negated)
        item = Item("i%03d" % len(items), entity, category, negated,
                    _item_text(entity, category, negated))
        items.append(item)
        by_key.setdefault(key, []).append(item)
        return item

    membership_items = {}  # (entity, category) -> item (non-negated)
    for entity in sorted(world.entity_leaf):
        leaf = world.entity_leaf[entity]
        chain = world.ancestors(leaf)  # leaf .. root
        for category in chain:
            membership_items[(entity, category)] = add_item(
                entity, category, False)
        # Two disjoint categories: a sibling of the leaf (if any) and
        # a category from an unrelated branch.
        siblings = [cat for cat in children.get(world.parent[leaf], [])
                    if cat != leaf]
        disjoint_choices = []
        if siblings:
            disjoint_choices.append(rng.choice(siblings))
        unrelated = [cat for cat in world.parent
                     if world.disjoint(cat, leaf)
                     and cat not in disjoint_choices]
        if unrelated:
            disjoint_choices.append(rng.choice(unrelated))
        for category in disjoint_choices:
            membership_items[(entity, category)] = add_item(
                entity, category, False)
        # Negation phrasings for the leaf and one disjoint category.
        add_item(entity, leaf, True)
        if disjoint_choices:
            add_item(entity, disjoint_choices[0], True)
        # A paraphrase of the leaf membership item.
        add_item(entity, leaf, False)

    relations = _declare_relations(world, items, by_key)
    return items, relations


def _declare_relations(world, items, by_key):
    """Direct relations only: parent-step subsets, sibling exclusion,
    negation pairs, paraphrase equivalence.  Transitive consequences
    are the auditor's job."""
    relations = []
    seen = set()

    def add(kind, first, second):
        marker = (kind, first.item_id, second.item_id)
        if first.item_id == second.item_id or marker in seen:
            return
        seen.add(marker)
        relations.append(Relation(kind, first.item_id, second.item_id))

    for item in items:
        entity, category, negated = item.key()
        # Subset: this proposition's category to its parent category,
        # for both polarities ("in child" implies "in parent";
        # "not in parent" implies "not in child" -- declared here as
        # the subset between the two negated propositions).
        parent = world.parent[category]
        if parent is not None:
            for target in by_key.get((entity, parent, negated), []):
                if negated:
                    add(REL_SUBSET, target, item)
                else:
                    add(REL_SUBSET, item, target)
        if not negated:
            # Exclusion between sibling categories.
            grandparent = world.parent[category]
            siblings = _children_map(world.parent).get(grandparent, [])
            for sibling in siblings:
                if sibling <= category:
                    continue
                for target in by_key.get((entity, sibling, False), []):
                    add(REL_EXCLUSION, item, target)
            # Negation pair.
            for target in by_key.get((entity, category, True), []):
                add(REL_NEGATION, item, target)
        # Equivalence between paraphrases (same key).
        for twin in by_key.get(item.key(), []):
            if twin.item_id > item.item_id:
                add(REL_EQUIVALENCE, item, twin)
    return relations


def semantic_implies(world, first, second):
    """Oracle: does literal ``first`` semantically imply ``second``?

    A literal is ``(item, value)`` -- the assertion that the item's
    answer is ``value``.  Each item asserts a value for the base
    membership variable of its (entity, category): the item's answer
    being ``value`` fixes membership to ``value XOR negated``.  The
    laminar category relations then decide implication.  This uses
    only the world tree, never the declared relations or the
    auditor's graph.
    """
    first_item, first_value = first
    second_item, second_value = second
    if first_item.entity != second_item.entity:
        return False
    first_membership = first_value ^ first_item.negated
    second_membership = second_value ^ second_item.negated
    cat_first = first_item.category
    cat_second = second_item.category
    if cat_first == cat_second:
        return first_membership == second_membership
    if world.is_ancestor(cat_second, cat_first):
        # cat_first sits below cat_second: membership propagates up
        # (in the child implies in the parent).  The contrapositive
        # (not in the parent implies not in the child) is the same
        # rule with the two literals swapped, so it is checked when
        # the ordered pair is swapped -- not here.
        return bool(first_membership and second_membership)
    if world.is_ancestor(cat_first, cat_second):
        # cat_second sits below cat_first: non-membership propagates
        # down (not in the parent implies not in the child).
        return bool((not first_membership)
                    and (not second_membership))
    # Disjoint categories: membership in one excludes the other.
    return bool(first_membership and not second_membership)


def ground_truth_violated_pairs(world, log):
    """Oracle violated pairs: unordered item pairs {i, j}, i != j,
    where one item's asserted literal semantically implies the
    negation of the other's asserted literal."""
    violated = set()
    items = log.items
    for left in range(len(items)):
        for right in range(left + 1, len(items)):
            first, second = items[left], items[right]
            first_lit = (first, log.answer(first.item_id))
            second_lit = (second, log.answer(second.item_id))
            first_neg = (first, not log.answer(first.item_id))
            second_neg = (second, not log.answer(second.item_id))
            if (semantic_implies(world, first_lit, second_neg)
                    or semantic_implies(world, second_lit, first_neg)):
                violated.add((first.item_id, second.item_id))
    return violated


def _confidence(rng, base):
    value = base + rng.uniform(-0.08, 0.08)
    return round(min(0.99, max(0.51, value)), 3)


def simulate_predictions(world, items, profile, seed):
    """Record a simulated predictor's answers over the items.

    Returns ``(predictions, planted_noisy)`` where ``planted_noisy``
    lists every item whose recorded answer differs from world truth.
    """
    spec = PROFILES[profile]
    rng = random.Random(3000007 * seed + 41)
    truth = dict((item.item_id, world.item_truth(item))
                 for item in items)
    answers = dict(truth)
    confidences = dict(
        (item.item_id, _confidence(rng, spec["confidence"]))
        for item in items)

    if profile == "consistent_liar":
        answers = _liar_answers(world, items, rng)
    else:
        for item in items:
            if rng.random() < spec["flip_p"]:
                answers[item.item_id] = not answers[item.item_id]
        if profile == "chain_breaker":
            _plant_chain_breaks(world, items, answers, confidences, rng)

    predictions = dict(
        (item_id, Prediction(answers[item_id], confidences[item_id]))
        for item_id in answers)
    planted = sorted(item_id for item_id in answers
                     if answers[item_id] != truth[item_id])
    return predictions, planted


def _liar_answers(world, items, rng):
    """Answers from an alternative consistent world: two entities
    are moved to a sibling leaf, so every answer stays consistent
    with every relation while many are wrong."""
    children = _children_map(world.parent)
    moved = {}
    entities = sorted(world.entity_leaf)
    rng.shuffle(entities)
    for entity in entities:
        if len(moved) >= 2:
            break
        leaf = world.entity_leaf[entity]
        siblings = [cat for cat in children.get(world.parent[leaf], [])
                    if cat != leaf]
        if siblings:
            moved[entity] = rng.choice(siblings)
    alt_leaf = dict(world.entity_leaf)
    alt_leaf.update(moved)
    alt_world = World(world.parent, alt_leaf)
    return dict((item.item_id, alt_world.item_truth(item))
                for item in items)


def _plant_chain_breaks(world, items, answers, confidences, rng):
    """Flip the top of a leaf-to-root chain to False while the leaf
    stays True: a contradiction visible only through the transitive
    subset chain (the direct neighbours still agree pairwise along
    most of the path)."""
    by_key = {}
    for item in items:
        by_key.setdefault(item.key(), []).append(item)
    entities = sorted(world.entity_leaf)
    rng.shuffle(entities)
    planted = 0
    for entity in entities:
        if planted >= 2:
            break
        leaf = world.entity_leaf[entity]
        chain = world.ancestors(leaf)
        if len(chain) < 3:
            continue
        top = chain[-1]
        top_items = by_key.get((entity, top, False), [])
        leaf_items = by_key.get((entity, leaf, False), [])
        if not top_items or not leaf_items:
            continue
        top_item = top_items[0]
        if answers[top_item.item_id]:
            answers[top_item.item_id] = False
            confidences[top_item.item_id] = 0.95
            planted += 1


def build_log(scenario, profile, seed):
    """Build one generated log plus its world (for the oracle)."""
    world = build_world(scenario, seed)
    items, relations = build_items(world, seed)
    predictions, planted = simulate_predictions(world, items, profile,
                                                seed)
    name = "%s-%s-%d" % (scenario, profile, seed)
    log = PredictionLog(
        name, items, relations, predictions, planted,
        meta={"scenario": scenario, "profile": profile, "seed": seed})
    return log, world
