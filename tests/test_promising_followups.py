from ai_lab.dream import followups


def _lead(category="high-level"):
    return {
        "lead_id": "lead-test", "key": "k", "category": category,
        "family": "white", "knobs": {
            "noise_amplitude": 1e-3, "correlation_length": 4.0,
            "diffusion_ratio": 1.0, "drive_strength": 2.0, "quench_duration": 8.0,
        },
        "baseline_level": 2, "status": "OPEN", "priority": 1.0, "times_selected": 0,
        "evidence": {
            "exact": {"n": 0, "success": 0}, "local": {"n": 0, "success": 0},
            "contrast": {"n": 0, "success": 0}, "native3d": {"n": 0, "success": 0},
            "geometry": {"n": 0, "triangle": 0, "fission_like": 0},
        },
        "honesty": {"status_changes_scientific_level": False, "status_changes_success_gate": False,
                    "followup_replaces_broad_exploration": False},
    }


def test_followup_plan_uses_fresh_seed_local_and_contrast_variants():
    specs = followups._variant_specs(_lead(), 20, master_seed=123)
    lanes = [x["followup_lane"] for x in specs]
    assert lanes.count("exact") == 8
    assert lanes.count("local") == 8
    assert lanes.count("contrast") == 4
    assert len({x["seed"] for x in specs}) == len(specs)


def test_repeated_then_robust_region_requires_many_exact_and_local_successes():
    lead = _lead()
    lead["evidence"]["exact"] = {"n": 16, "success": 12}
    lead["evidence"]["local"] = {"n": 16, "success": 9}
    followups._update_status(lead)
    assert lead["status"] == "ROBUST_REGION"


def test_weak_exact_reproduction_can_weaken_a_lead():
    lead = _lead()
    lead["evidence"]["exact"] = {"n": 20, "success": 2}
    followups._update_status(lead)
    assert lead["status"] == "WEAKENED"


def test_triangle_lead_is_only_repeated_observation_not_causality_claim():
    lead = _lead("triangle-fission")
    lead["evidence"]["geometry"] = {"n": 30, "triangle": 10, "fission_like": 5}
    followups._update_status(lead)
    assert lead["status"] == "REPEATED_OBSERVATION"
    assert "ROBUST" not in lead["status"]


def test_geometry_event_registers_a_triangle_followup_lead(tmp_path, monkeypatch):
    target = tmp_path / "leads.json"
    monkeypatch.setattr(followups, "_LEADS", target)
    doc = {"version": 1, "leads": []}
    probe = {
        "family": "sparse_seeds", "knobs": {
            "noise_amplitude": 1e-4, "correlation_length": 3.0,
            "diffusion_ratio": 0.5, "drive_strength": 2.5, "quench_duration": 9.0,
        },
        "seed": 7, "trial_index": 11, "triangle_seen": True, "fission_like_after_triangle": True,
    }
    result = followups.register_leads(doc, burst_id="dream-test", events=[], mass_results=[], paired3d=[], geometry_probes=[probe])
    assert result["added"] == 1
    assert doc["leads"][0]["category"] == "triangle-fission"
    assert doc["leads"][0]["honesty"]["followup_replaces_broad_exploration"] is False
