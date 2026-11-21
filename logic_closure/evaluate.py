"""The headline evaluation.

Seeded logs from every scenario x predictor profile are audited
blind (the auditor never sees the planted ground truth), then
scored against the independent world-semantics oracle:

- **Violation detection**: the auditor's violated pairs against the
  oracle's violated pairs (pooled precision / recall / F1), and the
  negation-only baseline's recall against the same oracle.
- **Transitive share**: of the violated pairs, how many have a
  shortest witness longer than one edge -- contradictions no
  pairwise check can see, baseline included.
- **Correction quality**: the minimal correction set against the
  planted noise -- exactness (size and set match against the planted
  flips that participate in conflicts), item-level precision/recall
  against *all* planted flips (recall is capped by construction:
  flips in slack positions and the consistent liar's flips create
  no contradiction and cannot be found), the greedy-vs-exact size
  gap, and a validity check (flipping the correction must leave
  zero violations).
- **Score ordering**: within each scenario/seed, does the
  confidence-weighted violation rate order the five predictor
  profiles the same way their planted flip counts do?
- **The blind spot**: the consistent liar's planted errors and how
  many the audit can see (by construction: none).
"""

import csv
import io
import json
import os

from .audit import audit_log
from .baseline import negation_baseline
from .correction import correction_for_audit
from .generate import PROFILES, SCENARIOS, build_log, \
    ground_truth_violated_pairs

DEFAULT_SEEDS = tuple(range(6))


def _score_log(log, world):
    audit = audit_log(log)
    truth_pairs = ground_truth_violated_pairs(world, log)
    found_pairs = audit.violated_pairs
    baseline = negation_baseline(log)
    correction = correction_for_audit(audit)
    planted = set(log.planted_noisy)
    conflict_planted = planted & set(audit.conflict_nodes)
    cover = set(correction["items"])

    corrected = log.flipped(cover)
    remaining = len(audit_log(corrected).violations)

    witness_by_pair = dict((violation.pair, violation)
                           for violation in audit.violations)
    transitive = 0
    for pair in truth_pairs & found_pairs:
        if not witness_by_pair[pair].direct:
            transitive += 1

    return {
        "name": log.name,
        "scenario": log.meta["scenario"],
        "profile": log.meta["profile"],
        "seed": log.meta["seed"],
        "n_items": len(log.items),
        "n_relations": len(log.relations),
        "n_linked_pairs": len(audit.linked_pairs),
        "gt_violated": len(truth_pairs),
        "found_violated": len(found_pairs),
        "tp": len(truth_pairs & found_pairs),
        "fp": len(found_pairs - truth_pairs),
        "fn": len(truth_pairs - found_pairs),
        "baseline_tp": len(baseline["violated_pairs"] & truth_pairs),
        "transitive_violated": transitive,
        "direct_violated": audit.direct_count,
        "violation_rate": audit.violation_rate,
        "weighted_violation_rate": audit.weighted_violation_rate,
        "planted": len(planted),
        "planted_rate": len(planted) / float(len(log.items)),
        "cover_size": correction["size"],
        "cover_exact": correction["exact"],
        "greedy_size": correction["greedy_size"],
        "cover_items": sorted(cover),
        "item_tp": len(cover & planted),
        "item_fp": len(cover - planted),
        "item_fn": len(planted - cover),
        "size_match": correction["size"] == len(conflict_planted),
        "set_match": cover == conflict_planted,
        "post_correction_violations": remaining,
    }


def run_evaluation(seeds=DEFAULT_SEEDS):
    rows = []
    for scenario in sorted(SCENARIOS):
        for profile in sorted(PROFILES):
            for seed in seeds:
                log, world = build_log(scenario, profile, seed)
                rows.append(_score_log(log, world))
    return _aggregate(rows)


def _aggregate(rows):
    tp = sum(row["tp"] for row in rows)
    fp = sum(row["fp"] for row in rows)
    fn = sum(row["fn"] for row in rows)
    precision = tp / float(tp + fp) if tp + fp else 1.0
    recall = tp / float(tp + fn) if tp + fn else 1.0
    f1 = (2.0 * precision * recall / (precision + recall)
          if precision + recall else 0.0)
    baseline_tp = sum(row["baseline_tp"] for row in rows)
    baseline_recall = baseline_tp / float(tp + fn) if tp + fn else 1.0
    detected = tp
    transitive = sum(row["transitive_violated"] for row in rows)

    item_tp = sum(row["item_tp"] for row in rows)
    item_fp = sum(row["item_fp"] for row in rows)
    item_fn = sum(row["item_fn"] for row in rows)
    item_precision = item_tp / float(item_tp + item_fp) \
        if item_tp + item_fp else 1.0
    item_recall = item_tp / float(item_tp + item_fn) \
        if item_tp + item_fn else 1.0

    conflict_rows = [row for row in rows if row["gt_violated"] > 0]
    exact_rows = [row for row in conflict_rows if row["cover_exact"]]
    greedy_gap = 0.0
    if exact_rows:
        greedy_gap = sum(row["greedy_size"] - row["cover_size"]
                         for row in exact_rows) / float(len(exact_rows))

    liar_rows = [row for row in rows
                 if row["profile"] == "consistent_liar"]
    liar_planted = sum(row["planted"] for row in liar_rows)
    liar_found = sum(row["found_violated"] for row in liar_rows)
    liar_items_found = sum(row["item_tp"] for row in liar_rows)

    per_profile = {}
    for profile in sorted(PROFILES):
        subset = [row for row in rows if row["profile"] == profile]
        p_tp = sum(row["tp"] for row in subset)
        p_fn = sum(row["fn"] for row in subset)
        p_item_tp = sum(row["item_tp"] for row in subset)
        p_item_fn = sum(row["item_fn"] for row in subset)
        per_profile[profile] = {
            "n_logs": len(subset),
            "mean_planted_rate":
                sum(row["planted_rate"] for row in subset)
                / float(len(subset)),
            "mean_violation_rate":
                sum(row["violation_rate"] for row in subset)
                / float(len(subset)),
            "mean_weighted_violation_rate":
                sum(row["weighted_violation_rate"] for row in subset)
                / float(len(subset)),
            "detection_recall":
                p_tp / float(p_tp + p_fn) if p_tp + p_fn else None,
            "item_recall":
                p_item_tp / float(p_item_tp + p_item_fn)
                if p_item_tp + p_item_fn else 1.0,
        }

    ordering = _ordering_accuracy(rows)

    return {
        "n_logs": len(rows),
        "scenarios": sorted(SCENARIOS),
        "profiles": sorted(PROFILES),
        "detection": {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": precision, "recall": recall, "f1": f1,
        },
        "baseline": {
            "recall": baseline_recall,
            "tp": baseline_tp,
        },
        "transitive_share": (transitive / float(detected)
                             if detected else 0.0),
        "transitive_violated": transitive,
        "correction": {
            "logs_with_conflicts": len(conflict_rows),
            "exact_searches": len(exact_rows),
            "size_match_rate":
                (sum(1 for row in conflict_rows if row["size_match"])
                 / float(len(conflict_rows))) if conflict_rows else 1.0,
            "set_match_rate":
                (sum(1 for row in conflict_rows if row["set_match"])
                 / float(len(conflict_rows))) if conflict_rows else 1.0,
            "item_precision": item_precision,
            "item_recall": item_recall,
            "greedy_minus_exact_mean": greedy_gap,
            "post_correction_violations":
                sum(row["post_correction_violations"] for row in rows),
        },
        "ordering": ordering,
        "blind_spot": {
            "profile": "consistent_liar",
            "planted_items": liar_planted,
            "violated_pairs_found": liar_found,
            "planted_items_found": liar_items_found,
        },
        "per_profile": per_profile,
        "rows": rows,
    }


def _ordering_accuracy(rows):
    """Within each (scenario, seed), compare every pair of profiles
    whose planted counts differ: does the confidence-weighted
    violation rate order them the same way?

    Reported twice: over all pairs, and as an ablation over pairs
    that do not involve the consistent liar -- the liar is *built*
    to defeat any consistency score, so the two numbers separate
    "the score misranks inconsistent predictors" from "the score is
    blind to consistent errors" (the blind spot proper)."""
    def _score(subset_rows):
        groups = {}
        for row in subset_rows:
            key = (row["scenario"], row["seed"])
            groups.setdefault(key, []).append(row)
        compared = 0
        score = 0.0
        for group in groups.values():
            for left in range(len(group)):
                for right in range(left + 1, len(group)):
                    first, second = group[left], group[right]
                    if first["planted"] == second["planted"]:
                        continue
                    compared += 1
                    planted_order = first["planted"] \
                        > second["planted"]
                    rate_order = first["weighted_violation_rate"] \
                        > second["weighted_violation_rate"]
                    if first["weighted_violation_rate"] \
                            == second["weighted_violation_rate"]:
                        score += 0.5
                    elif planted_order == rate_order:
                        score += 1.0
        return compared, (score / float(compared) if compared else 1.0)

    compared, accuracy = _score(rows)
    visible = [row for row in rows
               if row["profile"] != "consistent_liar"]
    compared_x, accuracy_x = _score(visible)
    return {
        "pairs_compared": compared,
        "accuracy": accuracy,
        "pairs_compared_excluding_blind_spot": compared_x,
        "accuracy_excluding_blind_spot": accuracy_x,
    }


def _summary_markdown(results):
    det = results["detection"]
    cor = results["correction"]
    blind = results["blind_spot"]
    lines = []
    lines.append("# Evaluation summary")
    lines.append("")
    lines.append("%d seeded logs (%s; profiles %s), audited blind "
                 "and scored against the world-semantics oracle."
                 % (results["n_logs"],
                    ", ".join(results["scenarios"]),
                    ", ".join(results["profiles"])))
    lines.append("")
    lines.append("- Violation detection: precision %.3f, recall %.3f, "
                 "F1 %.3f (%d tp, %d fp, %d fn)."
                 % (det["precision"], det["recall"], det["f1"],
                    det["tp"], det["fp"], det["fn"]))
    lines.append("- Negation-only baseline recall: %.3f."
                 % results["baseline"]["recall"])
    lines.append("- Transitive share of detected violations: %.3f "
                 "(%d of %d)."
                 % (results["transitive_share"],
                    results["transitive_violated"], det["tp"]))
    lines.append("- Correction: size match %.3f, set match %.3f over "
                 "%d logs with conflicts; item precision %.3f, item "
                 "recall %.3f; greedy minus exact %.2f items; "
                 "post-correction violations %d."
                 % (cor["size_match_rate"], cor["set_match_rate"],
                    cor["logs_with_conflicts"], cor["item_precision"],
                    cor["item_recall"], cor["greedy_minus_exact_mean"],
                    cor["post_correction_violations"]))
    lines.append("- Profile ordering accuracy of the weighted "
                 "violation rate: %.3f over %d pairs; excluding "
                 "pairs involving the consistent liar: %.3f over "
                 "%d pairs."
                 % (results["ordering"]["accuracy"],
                    results["ordering"]["pairs_compared"],
                    results["ordering"]
                    ["accuracy_excluding_blind_spot"],
                    results["ordering"]
                    ["pairs_compared_excluding_blind_spot"]))
    lines.append("- Blind spot (consistent liar): %d planted wrong "
                 "answers, %d violated pairs found, %d planted items "
                 "in any correction set."
                 % (blind["planted_items"],
                    blind["violated_pairs_found"],
                    blind["planted_items_found"]))
    lines.append("")
    lines.append("Per profile (mean planted flip rate -> mean "
                 "weighted violation rate):")
    for profile in results["profiles"]:
        entry = results["per_profile"][profile]
        det = entry["detection_recall"]
        det_text = "n/a (no violated pairs exist)" if det is None \
            else "%.3f" % det
        lines.append("- %s: planted %.3f, violation rate %.3f, "
                     "weighted %.3f, detection recall %s, item "
                     "recall %.3f."
                     % (profile, entry["mean_planted_rate"],
                        entry["mean_violation_rate"],
                        entry["mean_weighted_violation_rate"],
                        det_text,
                        entry["item_recall"]))
    lines.append("")
    return "\n".join(lines)


def write_evaluation(results, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    json_path = os.path.join(out_dir, "evaluation.json")
    with io.open(json_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, sort_keys=True)
    paths["json"] = json_path

    csv_path = os.path.join(out_dir, "evaluation.csv")
    fieldnames = ["name", "scenario", "profile", "seed", "n_items",
                  "n_relations", "n_linked_pairs", "gt_violated",
                  "found_violated", "tp", "fp", "fn", "baseline_tp",
                  "transitive_violated", "direct_violated",
                  "violation_rate", "weighted_violation_rate",
                  "planted", "planted_rate", "cover_size",
                  "cover_exact", "greedy_size", "item_tp", "item_fp",
                  "item_fn", "size_match", "set_match",
                  "post_correction_violations"]
    with io.open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in results["rows"]:
            writer.writerow(dict((key, row[key])
                                 for key in fieldnames))
    paths["csv"] = csv_path

    md_path = os.path.join(out_dir, "evaluation_summary.md")
    with io.open(md_path, "w", encoding="utf-8") as fh:
        fh.write(_summary_markdown(results))
    paths["summary"] = md_path
    return paths
