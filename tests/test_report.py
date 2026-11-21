"""Tests for the text report."""

from logic_closure.audit import audit_log
from logic_closure.generate import build_log
from logic_closure.report import format_audit_report


def test_report_contains_the_headline_lines():
    log, _world = build_log("standard", "chain_breaker", 3)
    report = format_audit_report(log, audit_log(log))
    assert "Logic Closure Contradiction Audit" in report
    assert "Closure violations: 13" in report
    assert "Minimal correction set" in report
    assert "transitive" in report


def test_report_for_consistent_log():
    log, _world = build_log("compact", "consistent_liar", 0)
    report = format_audit_report(log, audit_log(log))
    assert "Closure violations: 0" in report
    assert "Minimal correction set: 0" in report


def test_report_shows_witness_paths():
    log, _world = build_log("standard", "chain_breaker", 3)
    report = format_audit_report(log, audit_log(log))
    assert "-[subset]->" in report
