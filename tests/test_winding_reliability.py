"""Phase-winding reliability observer (LT-2) — synthetic known-answer tests. role V, physics-free."""
import numpy as np

from genesis.diagnostics.winding_reliability import winding_reliability as wr


def _wfield(n=32, w=0, amp=1.0):
    x = np.arange(n)
    return (amp * np.exp(1j * 2 * np.pi * w * x / n))[:, None] * np.ones((1, n))


def test_clean_W0_W1_W2_positive_controls():
    for w in (0, 1, 2):
        r = wr(_wfield(32, w))
        assert r["dominant_winding"] == w
        assert r["dominant_fraction"] > 0.999
        assert r["invalid_fraction"] == 0.0
        assert r["closed_loop_residual_max"] < 1e-6


def test_low_amplitude_line_is_invalidated():
    n = 32
    amp = np.abs(np.sin(np.pi * np.arange(n) / n))[:, None] * np.ones((1, n))   # amplitude hits 0 at x=0
    f = amp * np.exp(1j * 2 * np.pi * np.arange(n)[:, None] / n)
    r = wr(f)
    assert r["invalid_fraction"] > 0.0
    assert "low_amplitude" in r["invalid_reasons"]


def test_near_pi_edge_flagged_invalid():
    # a line with one genuine ~pi phase jump (ambiguous), otherwise unit amplitude
    n = 16
    phase = np.zeros(n)
    phase[n // 2:] = np.pi - 0.05      # a single near-pi step at the midpoint
    f = (np.exp(1j * phase))[:, None] * np.ones((1, n))
    r = wr(f, amp_frac=0.0)            # disable amplitude gate so we isolate the near-pi flag
    assert r["invalid_fraction"] > 0.0
    assert "near_pi_ambiguous" in r["invalid_reasons"]
    assert r["near_pi_edge_fraction"] > 0.0


def test_noise_monotonically_worsens_reliability():
    rng = np.random.default_rng(1)
    base = _wfield(48, 1)
    prev = -1.0
    for a in (0.0, 0.3, 0.7, 1.2):
        r = wr(base + a * (rng.standard_normal(base.shape) + 1j * rng.standard_normal(base.shape)))
        assert r["invalid_fraction"] >= prev - 1e-9
        prev = r["invalid_fraction"]


def test_thresholds_echoed_for_provenance():
    r = wr(_wfield(24, 1), amp_frac=0.3, near_pi_margin=0.2)
    assert abs(r["amp_frac"] - 0.3) < 1e-12 and abs(r["near_pi_margin"] - 0.2) < 1e-12
    assert r["amp_threshold"] > 0.0 and "line" in r["sign_convention"]


def test_dominant_fraction_is_over_valid_lines_only():
    """Half the lines dip to zero amplitude (invalid); dominant fraction is computed over the valid half."""
    n = 24
    ramp = np.ones((n, n))
    ramp[:, : n // 2] = np.abs(np.sin(np.pi * np.arange(n) / n))[:, None]   # left half has an amplitude zero
    f = ramp * np.exp(1j * 2 * np.pi * np.arange(n)[:, None] / n)
    r = wr(f)
    assert r["invalid_line_count"] >= n // 2 - 1
    assert r["dominant_winding"] == 1 and r["dominant_fraction"] > 0.999    # valid lines all read W=1
