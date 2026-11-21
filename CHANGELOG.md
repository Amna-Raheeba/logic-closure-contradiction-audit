# Changelog

## 0.1.0 — 2026-11-22

- Initial release.
- Seeded log generator: laminar category-tree worlds with entity
  membership propositions (subset chains, sibling exclusion,
  negation phrasings, paraphrases), declared direct relations only,
  and five simulated predictor profiles -- careful, typical, sloppy,
  a chain breaker planting transitive-only contradictions, and a
  consistent liar planting the audit's blind spot on purpose.
- Independent ground-truth oracle: violated pairs decided from the
  world tree's semantics, never from the auditor's graph, so
  detection precision/recall measure the instrument.
- Implication graph over literals with contrapositive edges for
  subset, negation, exclusion and equivalence relations; BFS
  reachability and shortest witness paths.
- Closure auditor: violated pairs with witnesses, direct vs
  transitive classification, broken-relation listing, raw and
  confidence-weighted violation rates over logically linked pairs,
  and the conflict graph.
- Minimal correction sets as exact minimum vertex cover
  (branch-and-bound with a matching lower bound, greedy fallback
  flagged past a node cap) plus a greedy cover for the
  greedy-vs-exact gap.
- Negation-only pairwise baseline, scored against the same oracle.
- Headline evaluation over 60 seeded logs: detection P 1.000 /
  R 0.879 vs baseline recall 0.153; 53.9% of violations transitive;
  correction set match 0.821; post-correction violations 0;
  consistent-liar blind spot measured at 111 planted errors, 0
  found.
- Streamlit dashboard (Audit / Correction / Evaluation tabs), CLI
  demo and evaluate commands, runnable notebooks, and a
  headline-drift reproduction guard.
