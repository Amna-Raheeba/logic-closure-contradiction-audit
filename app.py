"""Streamlit dashboard for logic-closure-contradiction-audit.

Three tabs:
1. Audit -- pick a scenario, predictor profile and seed; the log is
   generated and audited live, with the violation table and witness
   paths.
2. Correction -- the conflict graph and the minimal correction set
   for the same log: exact vs greedy sizes and the items to flip.
3. Evaluation -- the shipped aggregate results from
   results/evaluation.json: detection, the negation-only baseline,
   correction quality, and the consistent-liar blind spot.

Run:  streamlit run app.py
"""

import io
import json
import os

import pandas as pd
import streamlit as st

from logic_closure.audit import audit_log
from logic_closure.baseline import negation_baseline
from logic_closure.correction import correction_for_audit
from logic_closure.generate import PROFILES, SCENARIOS, build_log
from logic_closure.report import _witness_text

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_results():
    path = os.path.join(HERE, "results", "evaluation.json")
    if not os.path.exists(path):
        return None
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _violation_rows(log, audit):
    rows = []
    for violation in audit.violations:
        first, second = violation.pair
        rows.append({
            "pair": "%s x %s" % (first, second),
            "kind": "direct" if violation.direct else "transitive",
            "path_edges": violation.path_length,
            "conf_first": log.confidence(first),
            "conf_second": log.confidence(second),
            "witness": _witness_text(log, violation),
        })
    return rows


def main():
    st.title("Logic Closure Contradiction Audit")
    st.write("Audit a recorded prediction log for logical "
             "contradictions among linked items -- no model access "
             "needed.")

    scenario = st.selectbox("Scenario", sorted(SCENARIOS),
                            index=1)
    profile = st.selectbox("Predictor profile", sorted(PROFILES),
                           index=0)
    seed = st.number_input("Seed", min_value=0, max_value=99,
                           value=3)
    log, _world = build_log(scenario, profile, int(seed))
    audit = audit_log(log)
    correction = correction_for_audit(audit)

    tab_audit, tab_correction, tab_eval = st.tabs(
        ["Audit", "Correction", "Evaluation"])

    with tab_audit:
        st.metric("Closure violations", len(audit.violations))
        col1, col2, col3 = st.columns(3)
        col1.metric("Direct", audit.direct_count)
        col2.metric("Transitive", audit.transitive_count)
        col3.metric("Broken declared relations",
                    len(audit.broken_relations))
        st.metric("Violation rate (linked pairs)",
                  "%.3f" % audit.violation_rate)
        st.metric("Confidence-weighted violation rate",
                  "%.3f" % audit.weighted_violation_rate)
        baseline = negation_baseline(log)
        st.write("The negation-only baseline finds %d violated "
                 "pair(s) in this log; the closure audit finds %d."
                 % (len(baseline["violated_pairs"]),
                    len(audit.violations)))
        rows = _violation_rows(log, audit)
        if rows:
            st.dataframe(pd.DataFrame(rows))
        else:
            st.write("No closure violations: the recorded answers "
                     "are mutually consistent.")

    with tab_correction:
        st.metric("Conflict-graph items", len(audit.conflict_nodes))
        st.metric("Minimal correction set (exact search)",
                  correction["size"])
        st.metric("Greedy correction set", correction["greedy_size"])
        items = log.item_map()
        rows = []
        for item_id in correction["items"]:
            rows.append({
                "item": item_id,
                "text": items[item_id].text,
                "recorded": "yes" if log.answer(item_id) else "no",
                "confidence": log.confidence(item_id),
                "planted_noisy": item_id in log.planted_noisy,
            })
        if rows:
            st.dataframe(pd.DataFrame(rows))
        st.write("Flipping exactly these answers restores "
                 "consistency (verified by re-audit on the "
                 "generated logs); no smaller set can.")

    with tab_eval:
        results = _load_results()
        if results is None:
            st.write("No shipped results found. Run: python -m "
                     "logic_closure evaluate")
        else:
            det = results["detection"]
            cor = results["correction"]
            st.metric("Logs evaluated", results["n_logs"])
            col1, col2, col3 = st.columns(3)
            col1.metric("Detection precision",
                        "%.3f" % det["precision"])
            col2.metric("Detection recall", "%.3f" % det["recall"])
            col3.metric("Baseline recall",
                        "%.3f" % results["baseline"]["recall"])
            st.metric("Transitive share of violations",
                      "%.3f" % results["transitive_share"])
            st.metric("Correction set-match rate",
                      "%.3f" % cor["set_match_rate"])
            blind = results["blind_spot"]
            st.write("Blind spot: the consistent liar planted %d "
                     "wrong answers; the audit found %d violated "
                     "pairs.  A consistency audit cannot see "
                     "consistent errors."
                     % (blind["planted_items"],
                        blind["violated_pairs_found"]))
            profile_rows = []
            for name in results["profiles"]:
                entry = results["per_profile"][name]
                profile_rows.append({
                    "profile": name,
                    "planted_rate": entry["mean_planted_rate"],
                    "weighted_violation_rate":
                        entry["mean_weighted_violation_rate"],
                    "item_recall": entry["item_recall"],
                })
            frame = pd.DataFrame(profile_rows)
            st.dataframe(frame)
            st.bar_chart(frame.set_index("profile")
                         [["planted_rate",
                           "weighted_violation_rate"]])


if __name__ == "__main__":
    main()
