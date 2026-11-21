"""Audit the shipped demo log and print its report.

Run from the repository root:  python examples/run_audit.py
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic_closure.audit import audit_log
from logic_closure.models import PredictionLog
from logic_closure.report import format_audit_report


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "data", "demo_log.json")
    with io.open(path, encoding="utf-8") as fh:
        log = PredictionLog.from_dict(json.load(fh))
    audit = audit_log(log)
    sys.stdout.write(format_audit_report(log, audit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
