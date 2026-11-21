# Headline results

Across 60 seeded logs (2 scenarios x 5 predictor profiles x 6
seeds, 51-88 items and 75-126 declared relations per log), audited
blind and scored against an independent world-semantics oracle:

- **Violation detection: precision 1.000, recall 0.879, F1 0.936**
  (436 tp, 0 fp, 60 fn).  Every pair the auditor flags is a real
  contradiction; the misses are implications whose only derivation
  routes through a proposition the log never asked about -- closure
  is bounded by relation coverage, and the bound is measured, not
  hidden.
- **The negation-only baseline sees almost none of it: recall
  0.153.**  And **53.9% of the violations the auditor does find are
  transitive** (235 of 436) -- their shortest witness chains two or
  more declared relations, so no pairwise check of any single
  relation type can see them.
- **Minimal correction sets**: over the 39 logs with conflicts, the
  exact minimum vertex cover matches the planted noise's size in
  84.6% of logs and its exact set in 82.1%; item-level precision
  0.909, recall 0.449 (recall is capped by construction -- see the
  blind spot); the greedy cover never cost an extra item over the
  exact optimum on these graphs (mean gap 0.00); flipping the
  computed correction leaves **0** violations in every log.
- **Score ordering**: the confidence-weighted violation rate orders
  predictor profiles by their planted flip counts with accuracy
  0.897 over 68 pairs once the consistent liar is excluded -- and
  0.599 over all 116 pairs with it in.  The gap between those two
  numbers *is* the blind spot, priced.
- **The blind spot**: the consistent liar plants 111 wrong answers
  (the highest error rate of any profile, 15.3% of its items) and
  the audit finds **0** violated pairs and puts **0** of its items
  in any correction set.  A consistency audit cannot see consistent
  errors; this tool measures that limit instead of papering over
  it.

All numbers are measured on synthetic seeded logs under the
declared generator; see README section 8 for limits.
