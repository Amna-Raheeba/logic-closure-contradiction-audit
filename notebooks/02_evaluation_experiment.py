"""Notebook 02 -- the headline evaluation experiment.

Runs the seeded evaluation (2 scenarios x 5 predictor profiles x 6
seeds) and prints the aggregate detection, correction, ordering and
blind-spot numbers.  Runnable as a plain script:
python notebooks/02_evaluation_experiment.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic_closure.evaluate import run_evaluation


def main():
    results = run_evaluation()
    det = results["detection"]
    cor = results["correction"]
    blind = results["blind_spot"]
    print("Logs evaluated: %d" % results["n_logs"])
    print("Violation detection: P %.3f R %.3f F1 %.3f "
          "(tp %d, fp %d, fn %d)"
          % (det["precision"], det["recall"], det["f1"],
             det["tp"], det["fp"], det["fn"]))
    print("Negation-only baseline recall: %.3f"
          % results["baseline"]["recall"])
    print("Transitive share of detected violations: %.3f"
          % results["transitive_share"])
    print("Correction: size match %.3f, set match %.3f, item "
          "P %.3f / R %.3f, greedy-exact %.2f, post-correction "
          "violations %d"
          % (cor["size_match_rate"], cor["set_match_rate"],
             cor["item_precision"], cor["item_recall"],
             cor["greedy_minus_exact_mean"],
             cor["post_correction_violations"]))
    print("Ordering accuracy (weighted rate vs planted flips): %.3f "
          "over %d pairs; excluding the consistent liar: %.3f over "
          "%d pairs"
          % (results["ordering"]["accuracy"],
             results["ordering"]["pairs_compared"],
             results["ordering"]["accuracy_excluding_blind_spot"],
             results["ordering"]
             ["pairs_compared_excluding_blind_spot"]))
    print("Blind spot: %d planted wrong answers from the consistent "
          "liar, %d violated pairs found"
          % (blind["planted_items"], blind["violated_pairs_found"]))
    print("")
    for profile in results["profiles"]:
        entry = results["per_profile"][profile]
        det = entry["detection_recall"]
        det_text = "n/a" if det is None else "%.3f" % det
        print("  %s: planted %.3f -> weighted violation rate %.3f, "
              "detection recall %s, item recall %.3f"
              % (profile, entry["mean_planted_rate"],
                 entry["mean_weighted_violation_rate"],
                 det_text, entry["item_recall"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
