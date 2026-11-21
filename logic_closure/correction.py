"""Minimal correction sets.

Flipping one item's answer un-asserts both of its literals, so any
set of flips that restores consistency must touch every violated
pair -- the correction problem is a minimum vertex cover over the
conflict graph (nodes: items in some violation; edges: the
violations).  Minimum vertex cover is NP-hard in general, but a
conflict graph at eval-log scale is small: an exact branch-and-bound
search with a maximal-matching lower bound solves the generated
logs instantly.  When a graph exceeds the declared node cap, the
search falls back to the greedy cover and says so (``exact`` comes
back False) rather than pretending.

Whether flipping the cover leaves the log fully consistent is not
assumed: the evaluation re-audits every corrected log and reports
the remaining violations (zero on all 60 generated logs).

The greedy cover (repeatedly take the highest-degree node) is always
computed too, so the evaluation can price the greedy-versus-exact
gap instead of assuming it.
"""

EXACT_NODE_CAP = 42


def _degrees(nodes, edges):
    degree = dict((node, 0) for node in nodes)
    for first, second in edges:
        degree[first] += 1
        degree[second] += 1
    return degree


def greedy_vertex_cover(nodes, edges):
    """Greedy cover: repeatedly take the highest-degree node."""
    remaining = set(edges)
    cover = set()
    nodes = list(nodes)
    while remaining:
        degree = _degrees(nodes, remaining)
        pick = max(nodes, key=lambda node: (degree.get(node, 0), node))
        if degree.get(pick, 0) == 0:
            break
        cover.add(pick)
        remaining = set(edge for edge in remaining if pick not in edge)
    return cover


def _matching_lower_bound(edges):
    """Size of a greedy maximal matching: a valid lower bound on
    any vertex cover."""
    used = set()
    count = 0
    for first, second in sorted(edges):
        if first not in used and second not in used:
            used.add(first)
            used.add(second)
            count += 1
    return count


def _branch_and_bound(nodes, edges, best):
    """Exact minimum vertex cover by branching on one uncovered
    edge; ``best`` is the incumbent (a set) to beat."""
    best_cover = [set(best)]

    def search(remaining_edges, chosen):
        if not remaining_edges:
            if len(chosen) < len(best_cover[0]):
                best_cover[0] = set(chosen)
            return
        if len(chosen) + _matching_lower_bound(remaining_edges) \
                >= len(best_cover[0]):
            return
        first, second = sorted(remaining_edges)[0]
        for pick in (first, second):
            rest = set(edge for edge in remaining_edges
                       if pick not in edge)
            chosen.add(pick)
            search(rest, chosen)
            chosen.discard(pick)

    search(set(edges), set())
    return best_cover[0]


def min_vertex_cover(nodes, edges):
    """Return ``(cover, exact)``: a minimum vertex cover of the
    conflict graph, or the greedy cover flagged inexact when the
    graph exceeds the exact-search node cap."""
    nodes = sorted(set(nodes))
    edges = sorted(set(tuple(sorted(edge)) for edge in edges))
    if not edges:
        return set(), True
    greedy = greedy_vertex_cover(nodes, edges)
    if len(nodes) > EXACT_NODE_CAP:
        return greedy, False
    exact = _branch_and_bound(nodes, edges, greedy)
    return exact, True


def correction_for_audit(audit):
    """The minimal correction set for an audited log.

    Returns a dict with the exact (or greedy-flagged) cover, the
    greedy cover, and both sizes."""
    cover, exact = min_vertex_cover(audit.conflict_nodes,
                                    audit.conflict_edges)
    greedy = greedy_vertex_cover(audit.conflict_nodes,
                                 audit.conflict_edges)
    return {
        "items": sorted(cover),
        "size": len(cover),
        "exact": exact,
        "greedy_items": sorted(greedy),
        "greedy_size": len(greedy),
    }
