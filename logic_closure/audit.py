"""The closure auditor.

Given a recorded log, the auditor:

1. builds the implication graph over literals from the declared
   relations;
2. finds every *closure violation* -- an unordered pair of items
   whose asserted literals are linked by an implication path to a
   contradiction -- with a shortest witness path for each;
3. classifies each violation as *direct* (witness of length 1: a
   single declared relation is broken) or *transitive* (the break
   only appears after chaining relations, e.g. A=yes, A subset B,
   B subset C, C=no);
4. scores the log: the raw violation rate over all logically linked
   item pairs, and a confidence-weighted rate in which a violation
   between two confidently asserted answers counts more than one
   involving a hedged answer;
5. exposes the *conflict graph* (items as nodes, violations as
   edges) that the correction search in
   :mod:`logic_closure.correction` works on.

Direct relation breaks are also listed individually: a declared
relation is broken when the two recorded answers violate the
relation's own constraint, judged without any chaining.
"""

from .graph import ImplicationGraph, negate
from .models import (REL_EQUIVALENCE, REL_EXCLUSION, REL_NEGATION,
                     REL_SUBSET)


def relation_broken(relation, log):
    """True when the two recorded answers directly break a declared
    relation (no chaining involved)."""
    first = log.answer(relation.a)
    second = log.answer(relation.b)
    if relation.kind == REL_SUBSET:
        return first and not second
    if relation.kind == REL_NEGATION:
        return first == second
    if relation.kind == REL_EXCLUSION:
        return first and second
    if relation.kind == REL_EQUIVALENCE:
        return first != second
    return False


class Violation(object):
    """One contradictory pair of items, with its witness path."""

    __slots__ = ("pair", "witness", "path_kinds")

    def __init__(self, pair, witness, path_kinds):
        self.pair = pair                # (item_id, item_id), sorted
        self.witness = witness          # list of literals, asserted -> negated
        self.path_kinds = path_kinds    # relation kind per witness edge

    @property
    def path_length(self):
        return len(self.witness) - 1

    @property
    def direct(self):
        return self.path_length == 1


class AuditResult(object):
    __slots__ = ("log", "graph", "violations", "broken_relations",
                 "linked_pairs", "violation_rate",
                 "weighted_violation_rate", "conflict_nodes",
                 "conflict_edges")

    def __init__(self, log, graph, violations, broken_relations,
                 linked_pairs, violation_rate, weighted_rate,
                 conflict_nodes, conflict_edges):
        self.log = log
        self.graph = graph
        self.violations = violations
        self.broken_relations = broken_relations
        self.linked_pairs = linked_pairs
        self.violation_rate = violation_rate
        self.weighted_violation_rate = weighted_rate
        self.conflict_nodes = conflict_nodes
        self.conflict_edges = conflict_edges

    @property
    def violated_pairs(self):
        return set(violation.pair for violation in self.violations)

    @property
    def direct_count(self):
        return sum(1 for violation in self.violations
                   if violation.direct)

    @property
    def transitive_count(self):
        return sum(1 for violation in self.violations
                   if not violation.direct)

    @property
    def consistent(self):
        return not self.violations


def audit_log(log):
    graph = ImplicationGraph(log.items, log.relations)
    item_ids = [item.item_id for item in log.items]
    asserted = dict((item_id, (item_id, log.answer(item_id)))
                    for item_id in item_ids)

    reachability = dict(
        (item_id, graph.reachable(asserted[item_id]))
        for item_id in item_ids)
    all_reach = dict((literal, graph.reachable(literal))
                     for literal in graph.literals())

    # Linked pairs: some literal of one item implies some literal of
    # the other (in either direction).  These are the pairs the log's
    # relations actually constrain; the violation rate is taken over
    # them, not over all pairs.
    linked_pairs = set()
    for left in range(len(item_ids)):
        for right in range(left + 1, len(item_ids)):
            first, second = item_ids[left], item_ids[right]
            if _literals_linked(all_reach, first, second):
                linked_pairs.add((first, second))

    violations = []
    for first, second in sorted(linked_pairs):
        witness = _find_witness(graph, asserted, reachability,
                                first, second)
        if witness is None:
            continue
        kinds = []
        for step in range(len(witness) - 1):
            kinds.append(graph.edge_kind(witness[step],
                                         witness[step + 1]))
        violations.append(Violation((first, second), witness, kinds))

    broken = [relation for relation in log.relations
              if relation_broken(relation, log)]

    violated = set(violation.pair for violation in violations)
    if linked_pairs:
        violation_rate = len(violated) / float(len(linked_pairs))
    else:
        violation_rate = 0.0
    weighted = _weighted_rate(log, linked_pairs, violated)

    conflict_nodes = set()
    for first, second in violated:
        conflict_nodes.add(first)
        conflict_nodes.add(second)

    return AuditResult(log, graph, violations, broken, linked_pairs,
                       violation_rate, weighted, sorted(conflict_nodes),
                       sorted(violated))


def _literals_linked(all_reach, first, second):
    for first_value in (True, False):
        reached = all_reach[(first, first_value)]
        for second_value in (True, False):
            if (second, second_value) in reached:
                return True
    return False


def _find_witness(graph, asserted, reachability, first, second):
    """Shortest implication path from one item's asserted literal to
    the negation of the other's, in whichever direction exists."""
    candidates = []
    if negate(asserted[second]) in reachability[first]:
        path = graph.shortest_path(asserted[first],
                                   negate(asserted[second]))
        if path is not None:
            candidates.append(path)
    if negate(asserted[first]) in reachability[second]:
        path = graph.shortest_path(asserted[second],
                                   negate(asserted[first]))
        if path is not None:
            candidates.append(path)
    if not candidates:
        return None
    candidates.sort(key=len)
    return candidates[0]


def _weighted_rate(log, linked_pairs, violated_pairs):
    """Confidence-weighted violation rate: each linked pair carries
    weight conf_i * conf_j; the rate is the violated share of the
    total weight.  A contradiction between two confident answers
    counts more than one involving a hedge."""
    total = 0.0
    bad = 0.0
    for first, second in linked_pairs:
        weight = log.confidence(first) * log.confidence(second)
        total += weight
        if (first, second) in violated_pairs:
            bad += weight
    if total == 0.0:
        return 0.0
    return bad / total
