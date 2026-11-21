"""Build the shipped demo case: one standard chain_breaker log,
serialised with its planted ground truth, at data/demo_log.json,
plus the scenario/profile catalogue at data/scenarios.json.

Run from the repository root:  python scripts/build_cases.py
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic_closure.generate import PROFILES, SCENARIOS, build_log

DEMO_SCENARIO = "standard"
DEMO_PROFILE = "chain_breaker"
DEMO_SEED = 3


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log, _world = build_log(DEMO_SCENARIO, DEMO_PROFILE, DEMO_SEED)
    path = os.path.join(root, "data", "demo_log.json")
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump(log.to_dict(), fh, indent=2, sort_keys=True)
    print("Wrote %s (%d items, %d relations, %d planted noisy)"
          % (path, len(log.items), len(log.relations),
             len(log.planted_noisy)))

    scenarios = {
        "scenarios": SCENARIOS,
        "profiles": PROFILES,
        "demo": {"scenario": DEMO_SCENARIO, "profile": DEMO_PROFILE,
                 "seed": DEMO_SEED},
    }
    path = os.path.join(root, "data", "scenarios.json")
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump(scenarios, fh, indent=2, sort_keys=True)
    print("Wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
