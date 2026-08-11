"""Forbidden-vocabulary check for the R-layer (spec Sec.5).

Spec Sec.5 forbids using these words in R-layer result JSON/reports until the corresponding
instrument is defined/active for that result: 頻度/frequency (R4), 位相/phase (R7),
渦/vortex (R8), 次元/dimension (R9), 力/force + エネルギー/energy (never defined in the
R-layer), コヒーレンス/coherence (R10).

Through PR-R1.9, only R1-R4 existed, so nothing could license phase/vortex/dimension/force/
energy/coherence appearing anywhere in this codebase's output -- and R4's own "frequency"
was avoided by convention (stored under `rate` instead) so the test could be one flat,
mechanical "none of the seven words, anywhere" assertion.

PR-R2.2 adds R7 (phase, instruments.py::phase()) -- the first instrument in this codebase
licensed to use "phase"/位相. From here on this test has TWO parts, not one flat ban:
STILL_FORBIDDEN (渦/vortex, 次元/dimension, 力/force, エネルギー/energy, コヒーレンス/
coherence -- no instrument for any of these exists yet -- plus 頻度/frequency, which R4
still avoids purely by convention, unrelated to licensing) must never appear anywhere.
NOW_LICENSED (位相/phase) is licensed at the INSTRUMENT level, matching how R4's own
`name="period"` was always present on its Reading even when `defined=False` (undefined is
an honest "tried, precondition not met," not a claim of structure) -- R7's Reading always
carries `name="phase"`, defined or not, once the instrument exists. What matters is that
the license is actually EXERCISED, not merely permitted: a dedicated positive test below
confirms a real config produces a defined R7 reading that legitimately reports a phase
value, not just that the word is technically allowed to appear.
"""

import json

import numpy as np
import pytest

from ai_lab.relational import instrument_audit, instruments, substrate
from ai_lab.relational.run import build_result, _parser

STILL_FORBIDDEN_WORDS = [
    "頻度", "frequency",   # R4 exists but this codebase avoids the word by convention (rate)
    "渦", "vortex",         # R8 -- does not exist yet
    "次元", "dimension",    # R9 -- does not exist yet
    "力", "force",          # never defined in the R-layer
    "エネルギー", "energy",  # never defined in the R-layer
    "コヒーレンス", "coherence",  # R10 -- does not exist yet
]

NOW_LICENSED_WORDS = ["位相", "phase"]  # R7 (PR-R2.2) licenses these


def _scan(text: str, words=STILL_FORBIDDEN_WORDS):
    lowered = text.lower()
    hits = []
    for w in words:
        needle = w.lower()
        if needle in lowered:
            hits.append(w)
    return hits


@pytest.mark.parametrize("memory", ["off", "on"])
@pytest.mark.parametrize("saturation", ["none", "cubic"])
def test_run_output_never_emits_still_forbidden_words(memory, saturation):
    args = _parser().parse_args([
        "--n", "16", "--steps", "300", "--seed", "1",
        "--memory", memory, "--saturation", saturation,
    ])
    result = build_result(args)
    text = json.dumps(result, ensure_ascii=False)
    hits = _scan(text)
    assert not hits, "still-forbidden word(s) %r found in R-layer result JSON (memory=%s, saturation=%s)" % (
        hits, memory, saturation,
    )


def test_run_output_with_defined_R4_still_has_no_still_forbidden_words():
    # memory=on, low damping: R4 should actually become defined for this to be a meaningful check.
    args = _parser().parse_args([
        "--n", "20", "--steps", "2000", "--seed", "4", "--memory", "on", "--damping", "0.05",
    ])
    result = build_result(args)
    r4 = result["instruments"]["R4_period"]
    assert r4["defined"] is True, "test setup should produce a defined R4 reading to exercise the licensed case"
    text = json.dumps(result, ensure_ascii=False)
    hits = _scan(text)
    assert not hits, "still-forbidden word(s) %r found even though only R4 (never spelling out %r) is active" % (
        hits, "frequency",
    )


def test_instruments_module_reading_dicts_have_no_still_forbidden_words():
    res = substrate.run(n=14, steps=1500, seed=5, memory="on", damping=0.05)
    readings = instruments.measure_all(res.x_traj, res.W_initial, res.dt)
    for name, r in readings.items():
        text = json.dumps(r.to_dict(), ensure_ascii=False)
        hits = _scan(text)
        assert not hits, "still-forbidden word(s) %r found in %s Reading" % (hits, name)


def test_instrument_audit_verdicts_have_no_still_forbidden_words():
    res = substrate.run(n=14, steps=1500, seed=5, memory="on", damping=0.05)
    readings = instruments.measure_all(res.x_traj, res.W_initial, res.dt)
    verdicts = instrument_audit.audit_readings(readings)
    for name, v in verdicts.items():
        text = json.dumps(v.to_dict(), ensure_ascii=False)
        hits = _scan(text)
        assert not hits, "still-forbidden word(s) %r found in instrument_audit verdict for %s" % (hits, name)


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


def test_run_output_with_asymmetry_still_has_no_still_forbidden_words():
    """PR-R1.5: the new asymmetry axis and envelope (sustained/decaying/growing) output
    must not leak any still-forbidden word either -- exercises _envelope_trend's actual JSON."""
    args = _parser().parse_args([
        "--n", "16", "--steps", "1500", "--seed", "2", "--memory", "off",
        "--asymmetry", "--asymmetry-strength", "0.6",
    ])
    result = build_result(args)
    text = json.dumps(result, ensure_ascii=False)
    hits = _scan(text)
    assert not hits, "still-forbidden word(s) %r found in R-layer result JSON (asymmetry=True)" % hits


def test_run_output_undamped_sustained_still_has_no_still_forbidden_words():
    """Exercises the sustained=True path (envelope classification 'sustained') specifically."""
    args = _parser().parse_args([
        "--n", "16", "--steps", "3000", "--seed", "7", "--memory", "on", "--damping", "0.0",
    ])
    result = build_result(args)
    r4 = result["instruments"]["R4_period"]
    assert r4["value"]["any_sustained"] is True, "test setup should exercise the sustained=True path"
    text = json.dumps(result, ensure_ascii=False)
    hits = _scan(text)
    assert not hits, "still-forbidden word(s) %r found in R-layer result JSON (sustained path)" % hits


def test_run_output_memory_on_asymmetry_on_sustained_has_no_still_forbidden_words():
    """PR-R1.75: the memory=on x asymmetry=on regime is exactly the case most likely to
    tempt a leaked still-forbidden word (vortex/dimension/force/energy/coherence). Confirms
    the vocabulary discipline still holds on this specific output. This config uses
    saturation='none' deliberately -- AUDIT.md Sec.12.2 shows that setting cannot sustain
    genuinely, so R7 stays undefined here and this remains a still-forbidden-only check;
    the positive phase-licensing check below uses saturation='cubic' instead, where R7
    actually fires."""
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
    assert not hits, "still-forbidden word(s) %r found in R-layer result JSON (memory=on x asymmetry=on)" % hits


# ---------------------------------------------------------------------------
# PR-R2.2: R7 (phase) licenses 位相/phase. These tests confirm both directions of the
# license: absent when R7 is undefined, present when R7 fires -- not just "never forbidden."
# ---------------------------------------------------------------------------

def test_phase_word_present_when_r7_defined():
    """Positive licensing check: a config known (AUDIT.md Sec.13.6) to produce a
    verify_long_window-confirmed sustained_and_settled node must yield a defined R7 reading
    that legitimately uses 'phase' -- the license is exercised, not merely permitted."""
    res = substrate.run(n=24, steps=3000, dt=0.05, seed=5, memory="on", damping=0.05,
                         asymmetry=True, asymmetry_strength=0.3, topology="random_regular",
                         saturation="cubic", saturation_strength=0.1)
    readings = instruments.measure_all(res.x_traj, res.W_final, res.dt)
    r7 = readings["R7_phase"]
    assert r7.defined is True
    text = json.dumps(r7.to_dict(), ensure_ascii=False)
    assert "phase" in text.lower()
    # still-forbidden words must remain absent even in this phase-bearing output
    hits = _scan(text)
    assert not hits, "still-forbidden word(s) %r found alongside legitimate phase output" % hits


def test_r7_gates_on_r4_sustained_and_settled_per_node():
    res = substrate.run(n=24, steps=3000, dt=0.05, seed=5, memory="on", damping=0.05,
                         asymmetry=True, asymmetry_strength=0.3, topology="random_regular",
                         saturation="cubic", saturation_strength=0.1)
    readings = instruments.measure_all(res.x_traj, res.W_final, res.dt)
    r4, r7 = readings["R4_period"], readings["R7_phase"]
    for i, entry in enumerate(r7.value["per_node"]):
        r4_entry = r4.value["per_node"][i]
        if not r4_entry.get("sustained_and_settled", False):
            assert entry["defined"] is False


def test_r7_phase_rate_cross_checks_r4_autocorrelation_rate():
    """R7's phase-unwrapping rate and R4's autocorrelation-peak rate are two independent
    measurements of the same underlying quantity; they should roughly agree where both
    are defined -- a built-in consistency check, not merely two numbers reported side by
    side."""
    res = substrate.run(n=24, steps=3000, dt=0.05, seed=5, memory="on", damping=0.05,
                         asymmetry=True, asymmetry_strength=0.3, topology="random_regular",
                         saturation="cubic", saturation_strength=0.1)
    readings = instruments.measure_all(res.x_traj, res.W_final, res.dt)
    r4, r7 = readings["R4_period"], readings["R7_phase"]
    checked_any = False
    for i, entry in enumerate(r7.value["per_node"]):
        if not entry["defined"]:
            continue
        r4_rate = r4.value["per_node"][i]["rate"]
        r7_rate = entry["mean_rate_from_phase"]
        assert r4_rate is not None and r7_rate is not None
        assert abs(r7_rate - r4_rate) / r4_rate < 0.2
        checked_any = True
    assert checked_any, "test setup should exercise at least one R7-defined node"
