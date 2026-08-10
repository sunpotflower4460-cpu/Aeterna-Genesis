"""Forbidden-vocabulary check for the R-layer (spec Sec.5), scoped to PR-R1.

Spec Sec.5 forbids using these words in R-layer result JSON/reports until the corresponding
instrument is defined/active for that result: 頻度/frequency (R4), 位相/phase (R7),
渦/vortex (R8), 次元/dimension (R9), 力/force + エネルギー/energy (never defined in the
R-layer), コヒーレンス/coherence (R10).

PR-R1 only implements R1-R4. R5-R10 do not exist yet, so nothing could license
phase/vortex/dimension/force/energy/coherence appearing anywhere in this PR's output. R4
DOES exist and would license "frequency"/"頻度" -- but this PR's own instruments.py
deliberately never spells that word (it stores 1/T_i under the key `rate_i` instead; see
instruments.py's module docstring), specifically so this test can be the simpler, safer,
fully mechanical form the task allows: assert NONE of the seven words appear anywhere in
PR-R1's actual result output, full stop.
"""

import json

import numpy as np
import pytest

from ai_lab.relational import instrument_audit, instruments, substrate
from ai_lab.relational.run import build_result, _parser

FORBIDDEN_WORDS = [
    "頻度", "frequency",
    "位相", "phase",
    "渦", "vortex",
    "次元", "dimension",
    "力", "force",
    "エネルギー", "energy",
    "コヒーレンス", "coherence",
]


def _scan(text: str):
    lowered = text.lower()
    hits = []
    for w in FORBIDDEN_WORDS:
        needle = w.lower()
        if needle in lowered:
            hits.append(w)
    return hits


@pytest.mark.parametrize("memory", ["off", "on"])
@pytest.mark.parametrize("saturation", ["none", "cubic"])
def test_run_output_never_emits_forbidden_words(memory, saturation):
    args = _parser().parse_args([
        "--n", "16", "--steps", "300", "--seed", "1",
        "--memory", memory, "--saturation", saturation,
    ])
    result = build_result(args)
    text = json.dumps(result, ensure_ascii=False)
    hits = _scan(text)
    assert not hits, "forbidden word(s) %r found in R-layer result JSON (memory=%s, saturation=%s)" % (
        hits, memory, saturation,
    )


def test_run_output_with_defined_R4_still_has_no_forbidden_words():
    # memory=on, low damping: R4 should actually become defined for this to be a meaningful check.
    args = _parser().parse_args([
        "--n", "20", "--steps", "2000", "--seed", "4", "--memory", "on", "--damping", "0.05",
    ])
    result = build_result(args)
    r4 = result["instruments"]["R4_period"]
    assert r4["defined"] is True, "test setup should produce a defined R4 reading to exercise the licensed case"
    text = json.dumps(result, ensure_ascii=False)
    hits = _scan(text)
    assert not hits, "forbidden word(s) %r found even though only R4 (never spelling out %r) is active: %r" % (
        hits, "frequency", hits,
    )


def test_instruments_module_reading_dicts_have_no_forbidden_words():
    res = substrate.run(n=14, steps=1500, seed=5, memory="on", damping=0.05)
    readings = instruments.measure_all(res.x_traj, res.W_initial, res.dt)
    for name, r in readings.items():
        text = json.dumps(r.to_dict(), ensure_ascii=False)
        hits = _scan(text)
        assert not hits, "forbidden word(s) %r found in %s Reading" % (hits, name)


def test_instrument_audit_verdicts_have_no_forbidden_words():
    res = substrate.run(n=14, steps=1500, seed=5, memory="on", damping=0.05)
    readings = instruments.measure_all(res.x_traj, res.W_initial, res.dt)
    verdicts = instrument_audit.audit_readings(readings)
    for name, v in verdicts.items():
        text = json.dumps(v.to_dict(), ensure_ascii=False)
        hits = _scan(text)
        assert not hits, "forbidden word(s) %r found in instrument_audit verdict for %s" % (hits, name)


def test_r4_uses_rate_key_not_frequency_key():
    """Confirms the design choice: 1/T_i is measured but stored under 'rate', not 'frequency'."""
    dt = 0.05
    t = np.arange(0, 2000) * dt
    omega = 2 * np.pi / (40 * dt)
    series_a = np.sin(omega * t)
    series_b = np.sin(omega * t + 0.7)  # distinct phase so nodes differ (R1 > 0)
    x_traj = np.stack([series_a, series_b], axis=1)[:, :, None]
    r = instruments.period(x_traj, dt)
    node0 = r.value["per_node"][0]
    assert "rate" in node0
    assert "frequency" not in node0
    assert node0["rate"] is not None


def test_run_output_with_asymmetry_still_has_no_forbidden_words():
    """PR-R1.5: the new asymmetry axis and envelope (sustained/decaying/growing) output
    must not leak any forbidden word either -- exercises _envelope_trend's actual JSON."""
    args = _parser().parse_args([
        "--n", "16", "--steps", "1500", "--seed", "2", "--memory", "off",
        "--asymmetry", "--asymmetry-strength", "0.6",
    ])
    result = build_result(args)
    text = json.dumps(result, ensure_ascii=False)
    hits = _scan(text)
    assert not hits, "forbidden word(s) %r found in R-layer result JSON (asymmetry=True)" % hits


def test_run_output_undamped_sustained_still_has_no_forbidden_words():
    """Exercises the sustained=True path (envelope classification 'sustained') specifically,
    since 'phase' is exactly the kind of word an envelope/oscillation description could leak."""
    args = _parser().parse_args([
        "--n", "16", "--steps", "3000", "--seed", "7", "--memory", "on", "--damping", "0.0",
    ])
    result = build_result(args)
    r4 = result["instruments"]["R4_period"]
    assert r4["value"]["any_sustained"] is True, "test setup should exercise the sustained=True path"
    text = json.dumps(result, ensure_ascii=False)
    hits = _scan(text)
    assert not hits, "forbidden word(s) %r found in R-layer result JSON (sustained path)" % hits


def test_run_output_memory_on_asymmetry_on_sustained_has_no_forbidden_words():
    """PR-R1.75: the newly-found sustained regime (memory=on x asymmetry=on) is exactly
    the case most likely to tempt a leaked 'phase'/'frequency'/'winding' -- it is the
    R-layer's first genuine limit cycle. Confirms the vocabulary discipline still holds
    on this specific output, not just on the memory=on-alone positive control above."""
    args = _parser().parse_args([
        "--n", "24", "--steps", "3000", "--seed", "2", "--memory", "on", "--damping", "0.0",
        "--asymmetry", "--asymmetry-strength", "0.3", "--saturation", "none",
        "--topology", "random_regular",
    ])
    result = build_result(args)
    r4 = result["instruments"]["R4_period"]
    assert r4["value"]["any_sustained"] is True, "test setup should exercise the sustained=True path"
    text = json.dumps(result, ensure_ascii=False)
    hits = _scan(text)
    assert not hits, "forbidden word(s) %r found in R-layer result JSON (memory=on x asymmetry=on)" % hits
