"""Command line: demo audit of one generated log, or the full
evaluation."""

import argparse
import os

from .audit import audit_log
from .evaluate import run_evaluation, write_evaluation
from .generate import PROFILES, SCENARIOS, build_log
from .report import format_audit_report


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="logic_closure",
        description="Audit a recorded prediction log for logical "
                    "contradictions among linked items -- no model "
                    "access needed.")
    sub = parser.add_subparsers(dest="command")

    demo = sub.add_parser("demo", help="audit one generated log")
    demo.add_argument("--scenario", default="standard",
                      choices=list(SCENARIOS))
    demo.add_argument("--profile", default="chain_breaker",
                      choices=list(PROFILES))
    demo.add_argument("--seed", type=int, default=3)

    evaluate = sub.add_parser("evaluate", help="run the seeded "
                                               "evaluation")
    evaluate.add_argument("--out", default="results",
                          help="output directory")
    evaluate.add_argument("--seeds", type=int, default=6,
                          help="seeds per scenario/profile (0..n-1)")

    args = parser.parse_args(argv)

    if args.command == "evaluate":
        results = run_evaluation(seeds=tuple(range(args.seeds)))
        paths = write_evaluation(results, args.out)
        print("Wrote evaluation for %d logs to %s" % (
            results["n_logs"], os.path.abspath(args.out)))
        for key in sorted(paths):
            print("  %s: %s" % (key, paths[key]))
        det = results["detection"]
        print("Violation detection: P %.3f R %.3f F1 %.3f" % (
            det["precision"], det["recall"], det["f1"]))
        print("Negation-only baseline recall: %.3f"
              % results["baseline"]["recall"])
        print("Transitive share of violations: %.3f"
              % results["transitive_share"])
        return 0

    # Default: demo.
    scenario = getattr(args, "scenario", "standard")
    profile = getattr(args, "profile", "chain_breaker")
    seed = getattr(args, "seed", 3)
    log, _world = build_log(scenario, profile, seed)
    audit = audit_log(log)
    print(format_audit_report(log, audit))
    return 0
