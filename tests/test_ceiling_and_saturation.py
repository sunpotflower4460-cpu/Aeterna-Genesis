from __future__ import annotations

import json
from ai_lab.dream import adaptive, ceiling_ladder


def test_instrument_ceiling_is_measured_not_assumed():
    assert ceiling_ladder.instrument_max_level() == 2


def test_ladder_reports_instrument_limit(tmp_path):
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"search_discoveries": [{
        "family": "white", "seed": 42, "score": 2.7, "reached_level": 2,
        "knobs": {"noise_amplitude": 1e-3, "correlation_length": 4.0,
                  "diffusion_ratio": 1.0, "drive_strength": 2.0, "quench_duration": 8.0},
    }]}))
    r = ceiling_ladder.run_ladder(top=1, ladder=((48, 260, 10), (48, 520, 12)), workers=1, ledger_path=ledger)
    assert r["verdict"] == "instrument_limited"
    assert r["deeper_levels_are_unreportable_by_this_instrument"] is True
    assert r["honesty"]["flat_ladder_proves_a_physical_ceiling"] is False
    assert r["honesty"]["a_ceiling_at_the_instrument_maximum_is_a_physical_result"] is False


def test_saturation_reads_only_sample_count():
    atlas = {"regions": {
        "a": {"dimension": "2d", "tested": 900, "best_level": 2},
        "b": {"dimension": "2d", "tested": 900, "best_level": 0},
        "c": {"dimension": "2d", "tested": 3, "best_level": 2},
    }}
    assert adaptive.saturated_regions(atlas, min_trials=200) == {"a", "b"}


def test_random_floor_is_unchanged_by_saturation():
    allocation = dict(adaptive.DEFAULT_ALLOCATION)
    plain = adaptive.make_trial_plan(start_index=0, n=200, allocation=allocation, focus=None, master_seed=7)
    hot = {adaptive.plan_region_key(t["family"], t["knobs"]) for t in plain if t["lane"] == "unexplored"}
    steered = adaptive.make_trial_plan(start_index=0, n=200, allocation=allocation, focus=None, master_seed=7, saturated=hot)
    before = {t["trial_index"]: t for t in plain}
    assert any(t.get("resampled_from_saturated") for t in steered)
    for t in steered:
        if t["lane"] == "random":
            assert (t["family"], t["seed"]) == (before[t["trial_index"]]["family"], before[t["trial_index"]]["seed"])


def test_focus_saturation_cap_and_determinism():
    focus = {"family": "white", "knobs": {"noise_amplitude": 1e-3, "correlation_length": 4.0,
        "diffusion_ratio": 1.0, "drive_strength": 2.0, "quench_duration": 8.0}}
    alloc = dict(adaptive.DEFAULT_ALLOCATION)
    plain = adaptive.make_trial_plan(start_index=0, n=800, allocation=alloc, focus=focus, master_seed=5)
    hot = {adaptive.plan_region_key(t["family"], t["knobs"]) for t in plain if t["lane"] in ("hypothesis", "boundary", "breaker")}
    a = adaptive.make_trial_plan(start_index=0, n=800, allocation=alloc, focus=focus, master_seed=5, saturated=hot)
    b = adaptive.make_trial_plan(start_index=0, n=800, allocation=alloc, focus=focus, master_seed=5, saturated=hot)
    assert a == b and len(a) == 800
    inside = sum(1 for t in a if t["lane"] in ("hypothesis", "boundary", "breaker") and adaptive.plan_region_key(t["family"], t["knobs"]) in hot)
    assert inside <= int(800 * adaptive.SATURATED_FOCUS_SHARE)
    assert any(t.get("spilled_from_saturated_focus") for t in a)
