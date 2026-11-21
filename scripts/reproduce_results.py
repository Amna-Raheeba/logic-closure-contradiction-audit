"""Headline-drift guard.

Re-runs the full seeded evaluation and compares the aggregate
headline numbers against the shipped results/evaluation.json.
Exits non-zero if any headline value moved by more than the
tolerance -- i.e. if the code no longer reproduces the published
results.

Run from the repository root:  python scripts/reproduce_results.py
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic_closure.evaluate import run_evaluation

TOLERANCE = 0.02


def headline_values(results):
    det = results["detection"]
    cor = results["correction"]
    values = {
        "precision": det["precision"],
        "recall": det["recall"],
        "f1": det["f1"],
        "baseline_recall": results["baseline"]["recall"],
        "transitive_share": results["transitive_share"],
        "size_match_rate": cor["size_match_rate"],
        "set_match_rate": cor["set_match_rate"],
        "item_precision": cor["item_precision"],
        "item_recall": cor["item_recall"],
        "greedy_minus_exact_mean": cor["greedy_minus_exact_mean"],
        "ordering_accuracy": results["ordering"]["accuracy"],
        "ordering_accuracy_x_blind":
            results["ordering"]["accuracy_excluding_blind_spot"],
        "blind_planted": float(results["blind_spot"]["planted_items"]),
        "blind_found": float(results["blind_spot"]
                             ["violated_pairs_found"]),
    }
    for profile, entry in results["per_profile"].items():
        values["weighted_%s" % profile] = \
            entry["mean_weighted_violation_rate"]
        values["item_recall_%s" % profile] = entry["item_recall"]
        if entry["detection_recall"] is not None:
            values["detection_recall_%s" % profile] = \
                entry["detection_recall"]
    return values


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    shipped_path = os.path.join(root, "results", "evaluation.json")
    with io.open(shipped_path, encoding="utf-8") as fh:
        shipped = json.load(fh)
    fresh = run_evaluation()
    expected = headline_values(shipped)
    actual = headline_values(fresh)
    failures = []
    for key in sorted(expected):
        if key not in actual:
            failures.append("%s missing from fresh run" % key)
        elif abs(expected[key] - actual[key]) > TOLERANCE:
            failures.append(
                "%s: shipped %.4f vs fresh %.4f"
                % (key, expected[key], actual[key])
            )
    if failures:
        print("HEADLINE DRIFT DETECTED:")
        for failure in failures:
            print("  " + failure)
        return 1
    print("All %d headline values reproduce within %.2f."
          % (len(expected), TOLERANCE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
