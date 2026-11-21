"""The implication graph over literals.

Every declared relation compiles into directed edges between
literals ``(item_id, value)``:

- subset A, B:      A=yes -> B=yes;  B=no -> A=no (contrapositive)
- negation A, B:    A=yes -> B=no;   B=yes -> A=no;
                    A=no -> B=yes;   B=no -> A=yes
- exclusion A, B:   A=yes -> B=no;   B=yes -> A=no
- equivalence A, B: A=yes -> B=yes;  B=yes -> A=yes;
                    A=no -> B=no;    B=no -> A=no

A recorded answer *asserts* one literal per item.  The assignment
is inconsistent exactly when some asserted literal can reach the
negation of another asserted literal: everything on such a path is
forced by the log's own relations, so the two answers cannot both
stand.  Reachability and shortest witness paths are plain BFS --
the graph is small (two literals per item).
"""

from collections import deque

from .models import (REL_EQUIVALENCE, REL_EXCLUSION, REL_NEGATION,
                     REL_SUBSET)


def negate(literal):
    item_id, value = literal
    return (item_id, not value)


def _edges_for_relation(relation):
    a, b = relation.a, relation.b
    if relation.kind == REL_SUBSET:
        return [((a, True), (b, True)), ((b, False), (a, False))]
    if relation.kind == REL_NEGATION:
        return [((a, True), (b, False)), ((b, True), (a, False)),
                ((a, False), (b, True)), ((b, False), (a, True))]
    if relation.kind == REL_EXCLUSION:
        return [((a, True), (b, False)), ((b, True), (a, False))]
    if relation.kind == REL_EQUIVALENCE:
        return [((a, True), (b, True)), ((b, True), (a, True)),
                ((a, False), (b, False)), ((b, False), (a, False))]
    return []


class ImplicationGraph(object):
    """Adjacency over literals, with BFS reachability and witnesses."""

    def __init__(self, items, relations):
        self.adjacency = {}
        for item in items:
            self.adjacency.setdefault((item.item_id, True), set())
            self.adjacency.setdefault((item.item_id, False), set())
        self.edge_kinds = {}
        for relation in relations:
            for source, target in _edges_for_relation(relation):
                self.adjacency.setdefault(source, set()).add(target)
                self.adjacency.setdefault(target, set())
                self.edge_kinds.setdefault((source, target), set()).add(
                    relation.kind)

    def literals(self):
        return sorted(self.adjacency)

    def reachable(self, start):
        """All literals reachable from ``start`` (excluding itself,
        unless a cycle returns to it)."""
        seen = set()
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for nxt in self.adjacency.get(node, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return seen

    def shortest_path(self, start, goal):
        """A shortest literal path from ``start`` to ``goal``
        (inclusive), or None when unreachable."""
        if start == goal:
            return [start]
        parents = {start: None}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for nxt in sorted(self.adjacency.get(node, ())):
                if nxt in parents:
                    continue
                parents[nxt] = node
                if nxt == goal:
                    path = [goal]
                    cursor = node
                    while cursor is not None:
                        path.append(cursor)
                        cursor = parents[cursor]
                    path.reverse()
                    return path
                queue.append(nxt)
        return None

    def edge_kind(self, source, target):
        """The relation kind(s) that produced an edge, if recorded."""
        kinds = self.edge_kinds.get((source, target))
        if not kinds:
            return None
        return sorted(kinds)[0]
