# Logic Closure Contradiction Audit

## 1. What it is

A model's answers to an evaluation are usually scored one item at a
time. But eval items are rarely independent: a benchmark asks
whether an entity is in a category and also whether it is in the
parent category; it asks a question and its negation; it asks about
two mutually exclusive labels. A model can score well item by item
while its answers, taken together, describe something impossible --
yes to the child category, no to the parent; yes to a statement and
yes to its negation.

Those contradictions are sitting in the recorded log. Nobody needs
the model, its weights, or its API to find them -- only the log and
the logical relations between its items. Yet the standard
consistency check, when one is run at all, walks the negation pairs
and stops there.

This project is an offline audit instrument for the whole closure.
It reads a recorded prediction log, compiles the declared relations
between items into an implication graph, finds every pair of
answers that contradict each other *through any chain of
relations*, shows the witness path for each, scores the log, and
computes the smallest set of answers that would have to change to
make the log consistent again. Everything is deterministic and
seeded: the logs are synthetic, produced by simulated predictors
with planted error patterns, so the instrument itself is scored --
detection precision/recall against an independent oracle,
correction-set exactness against the planted noise -- instead of
merely demonstrated.

## 2. The novel mechanism

Four pieces, none of them a trained model:

1. **Implication-graph closure.** Each declared relation compiles
   to edges between literals (an item's answer being yes or no),
   with contrapositives: subset gives A=yes -> B=yes and
   B=no -> A=no; negation, exclusion and equivalence give their own
   edge sets. A pair of recorded answers is a *closure violation*
   when one answer's literal can reach the negation of the other's
   -- the two answers cannot both stand, however long the chain
   between them. Each violation carries a shortest witness path, so
   the output is not "this log is inconsistent" but "these two
   answers contradict, through exactly this chain".
2. **Direct vs transitive classification.** A violation whose
   witness is a single edge is a broken declared relation. Anything
   longer is invisible to every pairwise check -- it exists only in
   the closure. The audit reports the split, because the transitive
   share is the part of a model's inconsistency that standard
   practice structurally cannot see.
3. **Confidence-weighted violation rate.** Each logically linked
   pair carries weight conf_i x conf_j; the score is the violated
   share of the total weight. A contradiction between two answers
   given at 0.95 confidence counts more than one involving a hedge
   at 0.55 -- which is how a reader of the log experiences them.
4. **Minimal correction sets.** Flipping an answer un-asserts both
   its literals, so the fewest flips that restore consistency are a
   minimum vertex cover over the conflict graph (items as nodes,
   violations as edges). The tool solves it exactly by
   branch-and-bound (with a greedy fallback, flagged, past a node
   cap) and also computes the greedy cover, so the price of the
   cheap algorithm is measured rather than assumed.

## 3. How a log is represented

An item is a yes/no proposition with a recorded answer and a
confidence in [0.51, 0.99]. Relations are declared between items:

- **subset** -- A=yes implies B=yes (A's proposition is contained
  in B's);
- **negation** -- A and B are negations of each other and must
  disagree;
- **exclusion** -- A and B cannot both be yes;
- **equivalence** -- A and B must agree (paraphrases, restatements).

The generator builds logs from a small world -- a laminar category
tree, entities living in leaf categories, propositions about entity
membership -- and declares only the *direct* relations a real eval
harness would record: subset edges to the immediate parent
category, exclusion between sibling categories, negation pairs,
paraphrase equivalence. Everything transitive is left for the
auditor to derive, which is the point of the exercise.

## 4. The simulated predictors

Five profiles record answers over each world, each with planted
ground truth (the exact set of items whose answer differs from the
world truth):

- **careful** (2% flips), **typical** (6%), **sloppy** (13%) flip
  answers independently;
- **chain_breaker** flips the top of a leaf-to-root category chain
  while leaving the leaf asserted, planting contradictions whose
  witnesses are transitive by construction;
- **consistent_liar** answers from an alternative consistent world
  (entities quietly moved to a sibling leaf): the highest error
  rate of any profile, and zero contradictions. It exists to plant
  the audit's blind spot in the open.

## 5. The oracle problem, and how the evaluation avoids cheating

Scoring a closure auditor against ground truth is delicate: if the
"truth" is computed by the same graph the auditor uses, detection
is perfect by construction and the number means nothing. Here the
oracle is independent. The generator's world is a category tree,
and any two categories in a tree are either ancestor-related or
disjoint, so whether one item's answer semantically implies
another's is decidable from the tree alone -- no declared
relations, no implication graph. The evaluation compares the
auditor's violated pairs against the oracle's. If the graph
construction dropped an edge (a missing contrapositive, say), the
oracle would still know the implication holds and recall would
fall. It does fall, in an instructive place: see section 7.

## 6. The baseline

The comparison baseline is the standard quick pass: pairwise
negation checking only. It flags both endpoints of every broken
negation pair. It cannot see a subset break, an exclusion break, an
equivalence break, or anything transitive, and it offers no minimal
correction. It is scored against the same oracle as the auditor.

## 7. Measured results

60 seeded logs (2 scenarios x 5 profiles x 6 seeds; 51-88 items,
75-126 declared relations, 180-322 logically linked pairs per log),
audited blind:

- **Detection: precision 1.000, recall 0.879, F1 0.936** (436 tp,
  0 fp, 60 fn). Everything the auditor flags is a genuine
  contradiction. The 60 misses share one mechanism: the violated
  implication's only derivation routes through a proposition the
  log never asked about (for example, disjointness between two
  categories whose connecting sibling was never itself an item).
  Closure is bounded by the relation coverage of the log, and the
  bound shows up in recall exactly where coverage runs out --
  recall is 1.000 for the careful and chain_breaker profiles and
  0.83 for the denser typical and sloppy logs.
- **The baseline's recall is 0.153.** The negation-only pass misses
  about six of every seven contradictions the oracle knows about.
- **53.9% of detected violations are transitive** (235 of 436) --
  their shortest witnesses chain at least two declared relations.
- **Correction sets**: over the 39 logs with conflicts, the exact
  minimum cover matches the planted noise's size in 84.6% of logs
  and its exact set in 82.1% (when it differs, an equally small
  alternative cover exists -- the minimum is not always the planted
  set, and the evaluation says how often). Item-level precision
  0.909, recall 0.449; the greedy cover's mean size gap over the
  exact optimum is 0.00 items on these graphs; flipping the
  computed correction leaves **0 violations in all 60 logs**.
- **Ordering**: the confidence-weighted violation rate ranks the
  profiles by planted flip count with accuracy 0.897 over 68 pairs
  among the four inconsistent profiles -- and 0.599 over all 116
  pairs once the consistent liar is included. Per profile, mean
  planted rate -> mean weighted rate: careful 0.011 -> 0.009,
  chain_breaker 0.038 -> 0.055, typical 0.042 -> 0.035, sloppy
  0.105 -> 0.077, consistent_liar 0.153 -> 0.000.
- **The blind spot, priced**: the consistent liar plants 111 wrong
  answers across its 12 logs -- more errors than any other profile
  makes -- and the audit finds 0 violated pairs and places 0 of its
  items in any correction set. Item recall pooled across all
  profiles is 0.449 largely because of this: a large share of all
  planted errors are consistent ones, and no consistency audit can
  see them. The tool reports this as a headline, not a footnote.

Full per-log numbers ship in `results/evaluation.csv`; aggregates
in `results/evaluation.json` and `results/evaluation_summary.md`.

## 8. Honest limits

- **Consistent errors are invisible, by construction.** The audit
  measures logical consistency, not accuracy. A model that is
  coherently wrong -- the consistent liar is the extreme case --
  passes cleanly. The 0.599 all-pairs ordering accuracy is what
  that blindness costs as a ranking score; the tool's claim is the
  0.897 among predictors whose errors are not adversarially
  consistent, plus a measured price for the exception.
- **Recall is bounded by the log's relation coverage.** Detection
  recall of 0.879 is a property of these logs' declared relations
  (direct edges only, intermediate propositions sometimes absent).
  A log that declares more of its structure gives the closure more
  to work with; a log that declares only negation pairs reduces
  this tool to the baseline.
- **Item recall has a ceiling below 1 even for visible errors.** A
  flipped answer in a slack position (its relations are satisfied
  either way) creates no contradiction and cannot be found; and a
  minimum correction set is a *smallest* repair, not a recovery of
  the specific answers that were flipped -- set match is 0.821,
  not 1.000, partly because alternative optima exist.
- **The world is synthetic.** Laminar category trees make the
  oracle decidable; real benchmarks have messier relation webs
  (probabilistic implications, exceptions, relations that hold only
  approximately). The numbers validate the instrument and price its
  failure modes on this testbed; they are not a claim about any
  particular production benchmark.
- **Exact correction is exponential in the worst case.** Conflict
  graphs at eval-log scale solve instantly; a pathological log
  could exceed the node cap (42), in which case the tool returns
  the greedy cover and flags it inexact rather than hiding the
  substitution.

## 9. Prior art and the differentiator

CheckList (Ribeiro et al., ACL 2020) *generates* behavioural tests
to run against a live model; negation-robustness and consistency
papers (e.g. work probing whether models answer a question and its
negation coherently) test one relation type against a model they
can query. Both need the model. Nothing in that literature audits
an *existing* prediction log as a logical-closure problem: compile
whatever relations the log declares into an implication graph,
enumerate the closure violations with witnesses, weight them by
confidence, and compute the minimal correction set -- model-free,
on third-party logs, including published result tables. The
contribution here is that instrument, plus an evaluation in which
the auditor is scored against an oracle that shares no code with
it, and whose headline includes the instrument's own blind spot.

## 10. Usage

```bash
pip install pytest streamlit

# Audit one generated log (chain_breaker by default)
python -m logic_closure demo
python -m logic_closure demo --profile sloppy --seed 5

# Run the full seeded evaluation and write results/
python -m logic_closure evaluate --out results

# Audit the shipped demo log
python examples/run_audit.py

# Dashboard
streamlit run app.py

# Verify the shipped results still reproduce
python scripts/reproduce_results.py

# Tests
pytest
```

## 11. Project layout

- `logic_closure/models.py` -- items, relations, predictions, logs
- `logic_closure/generate.py` -- seeded worlds, declared relations,
  the world-semantics oracle, simulated predictor profiles
- `logic_closure/graph.py` -- the implication graph over literals
- `logic_closure/audit.py` -- closure violations, witnesses, scores
- `logic_closure/correction.py` -- exact and greedy minimal
  correction sets (minimum vertex cover over the conflict graph)
- `logic_closure/baseline.py` -- the negation-only pairwise check
- `logic_closure/evaluate.py` -- the headline evaluation
- `logic_closure/report.py` / `cli.py` -- text report and CLI
- `data/` -- the shipped demo log and the scenario catalogue
- `notebooks/` -- runnable demo and evaluation notebooks
- `examples/` -- an audit of the shipped demo log, with its output
- `results/` -- measured evaluation outputs and headline summary
- `tests/` -- the test suite

## 12. Author and license

Author: Amna Raheeba. MIT license (see `LICENSE`).
