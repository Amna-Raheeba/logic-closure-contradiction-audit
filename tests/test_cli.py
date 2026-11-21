"""Tests for the command line interface."""

import os

from logic_closure.cli import main


def test_default_command_is_demo(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Logic Closure Contradiction Audit" in out
    assert "standard-chain_breaker-3" in out


def test_demo_with_profile_and_seed(capsys):
    assert main(["demo", "--profile", "sloppy", "--seed", "5"]) == 0
    out = capsys.readouterr().out
    assert "standard-sloppy-5" in out


def test_evaluate_command_writes_results(tmp_path, capsys):
    out_dir = str(tmp_path / "results")
    assert main(["evaluate", "--out", out_dir, "--seeds", "1"]) == 0
    assert os.path.exists(os.path.join(out_dir, "evaluation.json"))
    assert os.path.exists(os.path.join(out_dir, "evaluation.csv"))
    assert os.path.exists(os.path.join(out_dir,
                                       "evaluation_summary.md"))
    out = capsys.readouterr().out
    assert "Violation detection" in out
