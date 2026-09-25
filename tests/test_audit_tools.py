"""P2 audit tools: the re-implemented X fingerprint must equal the detector's, and room classes are sane."""

import collections

import numpy as np

from ai_lab.dream import open_ended as oe
from tools.audit import rooms_index, xpattern_audit as xa


def test_fingerprint_matches_detector_at_default_thresholds():
    rng = np.random.default_rng(0)
    for _ in range(500):
        delta = rng.normal(0.0, 0.6, size=len(oe._FEATURES))
        assert xa.fingerprint(delta) == oe._episode_fingerprint(delta)


def test_static_class_reads_fingerprint_shape():
    assert xa.static_class("amp_std:+L|gradient_rms:+L|mean_amp:+L") == "AMPLITUDE_GROWTH"
    assert xa.static_class("amp_std:-S|defect_count:-M|spectral_anisotropy:-L") == "DEFECT_LOSS"
    assert xa.static_class("defect_count:+M") == "DEFECT_GAIN"
    assert xa.static_class("spectral_entropy:+L|spectral_k_rms:-M") == "SPECTRAL_REARRANGEMENT"


def test_labels_follow_defect_and_amplitude_changes():
    base = {"defect_count": 6.0, "net_topological_charge": 0.0, "mean_amp": 0.2}
    assert xa._label(base, {**base, "defect_count": 4.0}, 1.0) == "H1_pair_annihilation"
    assert xa._label(base, {**base, "defect_count": 0.0}, 1.0) == "H4_last_defects_vanish"
    assert xa._label(base, {**base, "defect_count": 5.0}, 1.0) == "H2_defect_count_change"
    assert xa._label(base, {**base, "mean_amp": 0.3}, 1.0) == "H3_amplitude_ordering"
    assert xa._label({**base, "mean_amp": 0.99}, {**base, "mean_amp": 1.0}, 1.0) == "H3b_amplitude_relaxation"


def _row(i, level, seed, drift=0.2, auto=True):
    return {"room_id": f"room-auto-dream-x-{i}" if auto else f"room-hand-{i}", "model": "g001", "dimension": 2,
            "noise_amplitude": 0.001, "quench_duration": 6.0, "correlation_length": 1.0,
            "initial_type": "uniform_plus_noise", "reached_level": level, "seed": seed,
            "conservation_drift": drift, "defect_count": 10, "auto_dream": auto}


def test_classify_keeps_representatives_outliers_and_hand_made_rooms():
    rows = [_row(i, 1, 100 + i) for i in range(20)] + [_row(20 + i, 2, 200 + i) for i in range(5)]
    rows.append(_row(99, 1, 999, drift=50.0))          # outlier inside the cell
    rows.append(_row(100, 1, 5, auto=False))           # hand-made
    rooms_index.classify(rows, collections.Counter())
    by_id = {r["room_id"]: r for r in rows}
    assert by_id["room-hand-100"]["class"] == "keep-full"
    assert "outlier" in by_id["room-auto-dream-x-99"]["reason"]
    assert by_id["room-auto-dream-x-20"]["class"] == "keep-full"      # min-seed representative of L2
    assert by_id["room-auto-dream-x-21"]["class"] == "distill"
    assert by_id["room-auto-dream-x-5"]["class"] == "index-only"
    assert all(r["class"] in {"keep-full", "distill", "index-only"} for r in rows)
