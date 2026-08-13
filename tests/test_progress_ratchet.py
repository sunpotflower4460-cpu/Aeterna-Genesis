import json

from ai_lab.dream import frontier_expander
from ai_lab.dream import progress_ratchet
from ai_lab.dream import research_optimizer


KNOBS = {
    "noise_amplitude": 4e-5,
    "correlation_length": 3.0,
    "diffusion_ratio": 0.4,
    "drive_strength": 2.0,
    "quench_duration": 8.0,
}


def _ranked(pid: str, score: float = 2.0, status: str = "REPEATED_SPECIFIC_CANDIDATE"):
    return {
        "pattern_id": pid,
        "score": score,
        "specificity": 0.8,
        "exact_rate": 0.7,
        "nearby_rate": 0.5,
        "contrast_rate": 0.0,
        "recent_studies": 0,
        "status": status,
        "search_focus": {"family": "white", "knobs": dict(KNOBS)},
        "row": {},
    }


def test_clipped_duplicate_conditions_share_one_question_key():
    knobs = dict(KNOBS)
    knobs["drive_strength"] = 5.0  # configured upper bound
    cells = progress_ratchet._candidate_cells(
        lane="x", target="X-edge", knobs=knobs, burst_id="b-edge"
    )
    drive = [c for c in cells if c["knob"] == "drive_strength"]
    at_cap = [c for c in drive if float(c["executed_value"]) == 5.0]
    assert len(at_cap) == 1
    assert at_cap[0]["progress_question_key"] == progress_ratchet._question_key(
        "x", "X-edge", "drive_strength", 5.0
    )
    assert len({c["progress_question_key"] for c in cells}) == len(cells)


def test_standard_low_high_controls_precede_refinement(monkeypatch):
    monkeypatch.setattr(progress_ratchet, "_durable_question_counts", lambda **kwargs: {})
    specs = progress_ratchet._ordered_specs(
        lane="x", target="X-test", family="white", knobs=dict(KNOBS),
        burst_id="b-standard-first", budget=4,
    )
    assert len(specs) == 4
    assert sum(s["intervened_knob"] is None for s in specs) == 2
    interventions = [s for s in specs if s["intervened_knob"] is not None]
    assert interventions[0]["intervened_knob"] == interventions[1]["intervened_knob"]
    assert [interventions[0]["progress_level"], interventions[1]["progress_level"]] == [
        "standard-low", "standard-high"
    ]
    assert all(int(s["progress_phase"]) == 0 for s in interventions)


def test_novelty_uses_full_retained_history_not_only_recent_window():
    key = progress_ratchet._question_key("x", "X-old", "drive_strength", 1.5)
    history = [{"progress": {"question_keys": [key]}}] + [{} for _ in range(20)]
    counts = progress_ratchet._durable_question_counts(history=history, memory={"entries": []})
    assert counts[key] == 1


def test_research_memory_keeps_question_known_beyond_ledger_lifetime():
    key = progress_ratchet._question_key("root", "RLAW-old", "relation_trend")
    memory = {
        "entries": [{
            "key": f"progress-question:{key}",
            "kind": "progress_question",
            "question_key": key,
            "times_seen": 3,
        }]
    }
    counts = progress_ratchet._durable_question_counts(history=[], memory=memory)
    assert counts[key] == 3


def test_inactive_lanes_do_not_accumulate_zero_gain():
    expansion = {
        "budget": {"executed": 2},
        "f_frontier_mechanism": {"experiments": 0, "results": []},
        "x_pattern_mechanism": {
            "experiments": 2,
            "patterns_studied": ["X-a"],
            "patterns": [{
                "pattern_id": "X-a",
                "sensitivity": [],
                "results": [
                    {
                        "intervened_knob": "drive_strength",
                        "progress_question_key": progress_ratchet._question_key(
                            "x", "X-a", "drive_strength", 1.5
                        ),
                    }
                ],
            }],
        },
        "root_operator_ablation": {"experiments": 0, "ablations": []},
    }
    audit = progress_ratchet._progress_audit(expansion, {}, [])
    assert "x" in audit["lane_knowledge_units"]
    assert "f" not in audit["lane_knowledge_units"]
    assert "root" not in audit["lane_knowledge_units"]


def test_nonfinite_f_screen_does_not_close_question():
    key = progress_ratchet._question_key("f", "white:7", "quench_duration", 10.0)
    expansion = {
        "budget": {"executed": 1},
        "f_frontier_mechanism": {
            "experiments": 1,
            "progress_target": "white:7",
            "results": [{
                "finite_screen": False,
                "counts_as_tested_question": False,
                "progress_question_key": key,
            }],
        },
        "x_pattern_mechanism": {"experiments": 0, "patterns": []},
        "root_operator_ablation": {"experiments": 0, "ablations": []},
    }
    audit = progress_ratchet._progress_audit(expansion, {}, [])
    assert key not in audit["question_keys"]
    assert key not in audit["new_question_keys"]
    assert audit["numerical_nonfinite_counts_as_negative_result"] is False


def test_recorded_next_burst_escape_is_actually_enforced_for_x(monkeypatch):
    history = [{
        "progress": {
            "next_burst_escape_required": True,
            "next_burst_escape_targets": ["x:X-a"],
        }
    }]
    monkeypatch.setattr(progress_ratchet, "_full_history", lambda: history)
    monkeypatch.setattr(progress_ratchet, "_memory", lambda: {"entries": []})
    monkeypatch.setattr(
        progress_ratchet, "_V9_RANK_X",
        lambda limit, history: [_ranked("X-a", 2.2), _ranked("X-b", 2.0)],
    )
    ranked = progress_ratchet.rank_x_focuses(limit=2, history=history)
    assert [r["pattern_id"] for r in ranked] == ["X-b"]


def test_replication_only_progress_requests_target_specific_escape():
    key = progress_ratchet._question_key("x", "X-a", "drive_strength", 1.5)
    expansion = {
        "budget": {"executed": 1},
        "f_frontier_mechanism": {"experiments": 0, "results": []},
        "x_pattern_mechanism": {
            "experiments": 1,
            "patterns_studied": ["X-a"],
            "patterns": [{
                "pattern_id": "X-a",
                "sensitivity": [],
                "results": [{
                    "intervened_knob": "drive_strength",
                    "progress_question_key": key,
                }],
            }],
        },
        "root_operator_ablation": {"experiments": 0, "ablations": []},
    }
    audit = progress_ratchet._progress_audit(expansion, {key: 1}, [])
    assert audit["status"] == "ADVANCED_BY_REPLICATION_ONLY"
    assert audit["next_burst_escape_required"] is True
    assert "x:X-a" in audit["next_burst_escape_targets"]
    assert audit["lane_knowledge_units"]["x"] == 0.0


def test_saturated_background_x_reopens_only_for_unseen_intervention(monkeypatch):
    memory = {
        "entries": [{
            "key": "x-saturated-background:X-a",
            "kind": "saturated_background_x",
            "avoid_exact_repeat": True,
        }]
    }
    monkeypatch.setattr(progress_ratchet, "_full_history", lambda: [])
    monkeypatch.setattr(progress_ratchet, "_memory", lambda: memory)
    monkeypatch.setattr(
        progress_ratchet, "_V9_RANK_X",
        lambda limit, history: [_ranked("X-a", 2.0, "REPEATED_NONSPECIFIC")],
    )
    monkeypatch.setattr(
        progress_ratchet, "_coverage",
        lambda lane, target, knobs, counts: {"seen": 10, "possible": 10, "unseen": 0, "fraction": 1.0},
    )
    assert progress_ratchet.rank_x_focuses(limit=1, history=[]) == []

    monkeypatch.setattr(
        progress_ratchet, "_coverage",
        lambda lane, target, knobs, counts: {"seen": 9, "possible": 10, "unseen": 1, "fraction": 0.9},
    )
    reopened = progress_ratchet.rank_x_focuses(limit=1, history=[])
    assert reopened[0]["pattern_id"] == "X-a"
    assert reopened[0]["research_memory_saturated_background"] is True


def test_progress_question_memory_preserves_existing_entries(tmp_path, monkeypatch):
    memory_path = tmp_path / "research_memory.json"
    memory_path.write_text(json.dumps({
        "version": 1,
        "entries": [{
            "key": "integrity:keep-me",
            "kind": "integrity_rule",
            "avoid_exact_repeat": False,
        }],
        "counts": {"total": 1},
        "policy": {},
    }))
    monkeypatch.setattr(progress_ratchet, "_MEMORY", memory_path)
    key = progress_ratchet._question_key("x", "X-new", "drive_strength", 1.4)
    progress_ratchet._persist_question_memory([key], burst_id="dream-test")
    saved = json.loads(memory_path.read_text())
    by_key = {row["key"]: row for row in saved["entries"]}
    assert "integrity:keep-me" in by_key
    q = by_key[f"progress-question:{key}"]
    assert q["kind"] == "progress_question"
    assert q["question_key"] == key
    assert q["avoid_exact_repeat"] is False
    assert saved["policy"]["progress_ratchet_reads_memory"] is True


def test_install_changes_planning_layer_only(monkeypatch):
    old_router = frontier_expander.run_frontier_expansion
    old_rank = research_optimizer.rank_x_focuses
    old_plan = research_optimizer._lane_plan
    old_specs = research_optimizer._balanced_x_specs
    old_study = research_optimizer._study_one_x
    old_f = frontier_expander._f_frontier_study
    old_root = frontier_expander._root_ablation_study
    try:
        progress_ratchet.install()
        assert frontier_expander.run_frontier_expansion is progress_ratchet.run_progressive_frontier_expansion
        assert research_optimizer.rank_x_focuses is progress_ratchet.rank_x_focuses
        assert research_optimizer._lane_plan is progress_ratchet._lane_plan
        assert research_optimizer._balanced_x_specs is progress_ratchet._balanced_x_specs
        assert research_optimizer._study_one_x is progress_ratchet._study_one_x
        assert frontier_expander._f_frontier_study is progress_ratchet._f_frontier_study
        assert frontier_expander._root_ablation_study is progress_ratchet._root_ablation_study
    finally:
        monkeypatch.setattr(frontier_expander, "run_frontier_expansion", old_router)
        monkeypatch.setattr(research_optimizer, "rank_x_focuses", old_rank)
        monkeypatch.setattr(research_optimizer, "_lane_plan", old_plan)
        monkeypatch.setattr(research_optimizer, "_balanced_x_specs", old_specs)
        monkeypatch.setattr(research_optimizer, "_study_one_x", old_study)
        monkeypatch.setattr(frontier_expander, "_f_frontier_study", old_f)
        monkeypatch.setattr(frontier_expander, "_root_ablation_study", old_root)
