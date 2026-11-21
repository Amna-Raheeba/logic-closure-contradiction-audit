# Evaluation summary

60 seeded logs (compact, standard; profiles careful, chain_breaker, consistent_liar, sloppy, typical), audited blind and scored against the world-semantics oracle.

- Violation detection: precision 1.000, recall 0.879, F1 0.936 (436 tp, 0 fp, 60 fn).
- Negation-only baseline recall: 0.153.
- Transitive share of detected violations: 0.539 (235 of 436).
- Correction: size match 0.846, set match 0.821 over 39 logs with conflicts; item precision 0.909, item recall 0.449; greedy minus exact 0.00 items; post-correction violations 0.
- Profile ordering accuracy of the weighted violation rate: 0.599 over 116 pairs; excluding pairs involving the consistent liar: 0.897 over 68 pairs.
- Blind spot (consistent liar): 111 planted wrong answers, 0 violated pairs found, 0 planted items in any correction set.

Per profile (mean planted flip rate -> mean weighted violation rate):
- careful: planted 0.011, violation rate 0.009, weighted 0.009, detection recall 1.000, item recall 0.778.
- chain_breaker: planted 0.038, violation rate 0.051, weighted 0.055, detection recall 1.000, item recall 0.931.
- consistent_liar: planted 0.153, violation rate 0.000, weighted 0.000, detection recall n/a (no violated pairs exist), item recall 0.000.
- sloppy: planted 0.105, violation rate 0.077, weighted 0.077, detection recall 0.828, item recall 0.706.
- typical: planted 0.042, violation rate 0.035, weighted 0.035, detection recall 0.832, item recall 0.788.
