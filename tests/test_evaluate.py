"""Tests for the headline evaluation (small, fast slices)."""

from logic_closure.evaluate import run_evaluation, write_evaluation


def test_evaluation_structure():
    results = run_evaluation(seeds=(0,))
    assert results["n_logs"] == 10
    for key in ("detection", "baseline", "transitive_share",
                "correction", "ordering", "blind_spot",
                "per_profile", "rows"):
        assert key in results
    assert len(results["rows"]) == 10


def test_detection_precision_is_perfect_on_slice():
    # The implication graph only contains edges compiled from
    # relations that are true in the world, so a flagged pair is
    # always a real contradiction.
    results = run_evaluation(seeds=(0, 1))
    assert results["detection"]["precision"] == 1.0
    assert results["detection"]["fp"] == 0


def test_baseline_recall_below_auditor_recall():
    results = run_evaluation(seeds=(0, 1))
    assert results["baseline"]["recall"] \
        < results["detection"]["recall"]


def test_post_correction_violations_are_zero():
    results = run_evaluation(seeds=(0, 1))
    assert results["correction"]["post_correction_violations"] == 0


def test_blind_spot_finds_nothing():
    results = run_evaluation(seeds=(0, 1))
    blind = results["blind_spot"]
    assert blind["planted_items"] > 0
    assert blind["violated_pairs_found"] == 0
    assert blind["planted_items_found"] == 0


def test_ordering_ablation_beats_pooled():
    results = run_evaluation(seeds=(0, 1, 2))
    ordering = results["ordering"]
    assert ordering["accuracy_excluding_blind_spot"] \
        >= ordering["accuracy"]


def test_write_evaluation_outputs(tmp_path):
    results = run_evaluation(seeds=(0,))
    paths = write_evaluation(results, str(tmp_path))
    for key in ("json", "csv", "summary"):
        assert key in paths
        with open(paths[key]) as fh:
            assert fh.read()
