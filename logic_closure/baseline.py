"""The baseline: pairwise negation checking only.

This is what a quick consistency pass over an eval log usually
amounts to -- walk the declared negation pairs and flag the ones
whose two answers agree when they should differ.  It cannot see a
subset break, an exclusion break, an equivalence break, or anything
that only contradicts through a chain, and it offers no minimal
correction: it flags both endpoints of every broken pair.

The evaluation scores this baseline against the same ground truth
as the closure auditor, so the gap between the two is measured, not
asserted.
"""

from .audit import relation_broken
from .models import REL_NEGATION


def negation_baseline(log):
    """Return ``{"violated_pairs": set, "flagged_items": set}`` for
    the negation-only pairwise check."""
    violated = set()
    flagged = set()
    for relation in log.relations:
        if relation.kind != REL_NEGATION:
            continue
        if relation_broken(relation, log):
            pair = tuple(sorted((relation.a, relation.b)))
            violated.add(pair)
            flagged.add(relation.a)
            flagged.add(relation.b)
    return {"violated_pairs": violated, "flagged_items": flagged}
