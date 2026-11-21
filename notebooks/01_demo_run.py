"""Notebook 01 -- demo run.

Build two contrasting logs (a chain_breaker, whose contradictions
hide in transitive chains, and a careful predictor), audit each, and
print the reports.  Runnable as a plain script:
python notebooks/01_demo_run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic_closure.audit import audit_log
from logic_closure.generate import build_log
from logic_closure.report import format_audit_report


def main():
    for profile in ("chain_breaker", "careful"):
        log, _world = build_log("standard", profile, 3)
        audit = audit_log(log)
        print(format_audit_report(log, audit))
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
