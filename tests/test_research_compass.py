import json

from ai_lab.dream import research_compass


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _install_paths(monkeypatch, tmp_path):
    paths = {
        "_EASY": tmp_path / "easy.json",
        "_EMERGENCE": tmp_path / "emergence.json",
        "_CROSSWORLD": tmp_path / "cross.json",
        "_MULTIWORLD": tmp_path / "multi.json",
        "_UNKNOWN": tmp_path / "unknown.json",
        "_DEEP": tmp_path / "deep.json",
        "_GOAL": tmp_path / "goal.json",
        "_MEMORY": tmp_path / "memory.json",
        "_REPORT_JSON": tmp_path / "compass.json",
        "_REPORT_MD": tmp_path / "compass.md",
        "_ROOT_MD": tmp_path / "CURRENT_RESEARCH.md",
    }
    for name, path in paths.items():
        monkeypatch.setattr(research_compass, name, path)
    return paths


def _fixtures(paths):
    _write(paths["_EASY"], {
        "burst_id": "dream-test-1",
        "geometry_summary": {
            "persistent_pair_seen": 31,
            "persistent_pair_only_seen": 21,
            "triad_local_energy_measured": 23,
            "pair_charge_patterns_measured": {"++": 1, "+-": 29, "--": 1},
            "triad_charge_patterns_measured": {"++-": 9, "+--": 14},
            "energy_asymmetry_peak_preceded_geometry_collapse": 0,
        },
        "human_summary": {
            "current_position": "名無し変化の成立条件を絞っている段階です。",
            "achieved_this_time": ["条件を変えて消えるかを調べました。"],
        },
    })
    _write(paths["_EMERGENCE"], {
        "burst_id": "dream-test-1",
        "recurrent_unlabeled_patterns": 111,
        "top_recurrent": [{
            "pattern_id": "X-broad",
            "observations": 642,
            "seeds": list(range(64)),
            "conditions": [f"c{i}" for i in range(64)],
            "representative": {"zero_purity": "scaffolded-start"},
        }],
    })
    _write(paths["_UNKNOWN"], {"patterns": {
        "X-specific": {
            "status": "REPEATED_SPECIFIC_CANDIDATE",
            "exact": {"hit": 11, "n": 15},
            "local": {"hit": 10, "n": 15},
            "contrast": {"hit": 0, "n": 15},
            "search_focus": {"family": "white"},
        },
        "X-broad": {
            "status": "REPEATED_NONSPECIFIC",
            "exact": {"hit": 29, "n": 38},
            "local": {"hit": 22, "n": 38},
            "contrast": {"hit": 1, "n": 38},
            "search_focus": {"family": "single_seed"},
        },
        "X-old-fail": {
            "status": "WEAKENED",
            "exact": {"hit": 0, "n": 3},
            "local": {"hit": 0, "n": 3},
            "contrast": {"hit": 0, "n": 3},
            "search_focus": {"family": "white"},
        },
    }})
    _write(paths["_CROSSWORLD"], {
        "strict_zero_aligned_matches": 1,
        "g001_pattern_matches": [{
            "g001_pattern_id": "X-cross",
            "projection_coverage": 1.0,
            "g001_start_purities": ["Z-A:minimal-white"],
            "matched_worlds": ["o3-vector"],
            "matched_world_zero_pairs": ["o3-vector@Z-A"],
            "status": "CROSS_WORLD_ZERO_ALIGNED_LEAD",
        }],
    })
    _write(paths["_MULTIWORLD"], {"mode": "shadow"})
    _write(paths["_DEEP"], {"last_burst": "dream-test-1", "leads": [
        {
            "lead_id": "deep-stable",
            "baseline_F_depth": 4,
            "last_rung": 64.0,
            "status": "STABLE_THROUGH_64TAU",
            "history": [{"finite": True, "F_depth": 4}],
        },
        {
            "lead_id": "deep-current",
            "last_burst": "dream-test-1",
            "prefix_identity_status": "MATCH",
            "status": "VERIFYING",
            "history": [{"finite": True, "scientific_usable": True, "F_depth": 4}],
        },
        {
            "lead_id": "deep-quarantine",
            "status": "VERIFYING",
            "history": [{"finite": True, "scientific_usable": False, "legacy_semantics_unverified": True, "F_depth": 1}],
        },
    ]})
    _write(paths["_GOAL"], {"goal_reached": False, "required_satisfied": 0, "required_total": 10})


def test_specific_candidate_is_front_page_before_broad_recurrence(monkeypatch, tmp_path):
    paths = _install_paths(monkeypatch, tmp_path)
    _fixtures(paths)
    compass, _ = research_compass.build_compass(now="2026-08-13T00:00:00+00:00")
    cards = compass["important_discoveries"]
    assert cards[0]["kind"] == "unicellular_bag_front"
    assert cards[0]["evidence_status"] == "ORIENTATION"
    assert "life" in cards[0]["not_claimed"]
    assert cards[1]["kind"] == "condition_specific_unknown_transition"
    assert "X-specific" in cards[1]["title"]
    assert any(x["kind"] == "robust_background_transition" for x in cards)
    assert any(x["kind"] == "cross_world_zero_aligned" for x in cards)


def test_failure_details_stay_in_machine_memory_but_human_digest_is_light(monkeypatch, tmp_path):
    paths = _install_paths(monkeypatch, tmp_path)
    _fixtures(paths)
    compass, memory = research_compass.build_compass(now="2026-08-13T00:00:00+00:00")
    weakened = [x for x in memory["entries"] if x.get("kind") == "weakened_x"]
    quarantined = [x for x in memory["entries"] if x.get("kind") == "deep_time_quarantine"]
    assert any(x["key"] == "x-weakened:X-old-fail" and x["avoid_exact_repeat"] for x in weakened)
    assert quarantined
    text = research_compass.render_markdown(compass)
    assert "X-old-fail" not in text
    assert "同じことを繰り返さない" in text
    assert "証拠は削除" in text


def test_memory_is_append_preserving_and_does_not_forget_old_lessons(monkeypatch, tmp_path):
    paths = _install_paths(monkeypatch, tmp_path)
    _fixtures(paths)
    _write(paths["_MEMORY"], {
        "entries": [{
            "key": "old:lesson",
            "kind": "historical_constraint",
            "human_short": "古い教訓",
            "times_seen": 7,
            "first_seen_burst": "old",
        }]
    })
    _, memory = research_compass.build_compass(now="2026-08-13T00:00:00+00:00")
    old = [x for x in memory["entries"] if x["key"] == "old:lesson"]
    assert len(old) == 1
    assert old[0]["times_seen"] == 7


def test_memory_preserves_progress_ratchet_schema_counts_and_policy(monkeypatch, tmp_path):
    paths = _install_paths(monkeypatch, tmp_path)
    _fixtures(paths)
    _write(paths["_MEMORY"], {
        "version": 2,
        "purpose": "compact-do-not-repeat-and-interpretation-memory",
        "entries": [{
            "key": "progress-question:x|X-specific|drive_strength|2",
            "kind": "progress_question",
            "question_key": "x|X-specific|drive_strength|2",
            "times_seen": 3,
            "first_seen_burst": "dream-old",
            "scientific_test_completed": True,
        }],
        "counts": {"progress_questions": 1, "custom_counter": 9},
        "policy": {
            "progress_ratchet_reads_memory": True,
            "progress_question_history_is_durable": True,
            "custom_policy": "keep-me",
        },
    })
    _, memory = research_compass.build_compass(now="2026-08-13T00:00:00+00:00")
    assert memory["version"] >= 2
    assert memory["counts"]["progress_questions"] == 1
    assert memory["counts"]["custom_counter"] == 9
    assert memory["policy"]["progress_ratchet_reads_memory"] is True
    assert memory["policy"]["progress_question_history_is_durable"] is True
    assert memory["policy"]["custom_policy"] == "keep-me"
    progress = [x for x in memory["entries"] if x.get("kind") == "progress_question"]
    assert len(progress) == 1
    assert progress[0]["times_seen"] == 3


def test_next_question_uses_live_recurrent_x_count(monkeypatch, tmp_path):
    paths = _install_paths(monkeypatch, tmp_path)
    _fixtures(paths)
    emergence = json.loads(paths["_EMERGENCE"].read_text())
    emergence["recurrent_unlabeled_patterns"] = 137
    _write(paths["_EMERGENCE"], emergence)
    compass, _ = research_compass.build_compass(now="2026-08-13T00:00:00+00:00")
    assert compass["highest_value_next_questions"][0] == research_compass._UNICELLULAR_NEXT
    assert any("137種類規模" in x for x in compass["highest_value_next_questions"])
    assert not any("111種類規模" in x for x in compass["highest_value_next_questions"])


def test_pinned_lanes_survive_in_human_markdown(monkeypatch, tmp_path):
    paths = _install_paths(monkeypatch, tmp_path)
    _fixtures(paths)
    compass, memory = research_compass.build_compass(now="2026-08-13T00:00:00+00:00")
    text = research_compass.render_markdown(compass)
    assert "三つの仕事を混ぜない" in text
    assert "単細胞／袋" in text
    assert "PR 133" in text
    assert "PR 134" in text
    assert "暗い芯を身体と数えない" in text
    assert compass["headline"] == research_compass._UNICELLULAR_HEADLINE
    assert compass["lanes"]["lead"] == "unicellular-bag"
    assert compass["integrity"]["vortex_hole_is_unicellular_bag"] is False
    assert compass["integrity"]["torus_is_required_for_a_body"] is False
    holes = [x for x in memory["entries"] if x.get("key") == "integrity:holes-are-not-bags"]
    assert len(holes) == 1
    assert "穴" in holes[0]["human_short"]


def test_local_energy_card_keeps_causal_limit(monkeypatch, tmp_path):
    paths = _install_paths(monkeypatch, tmp_path)
    _fixtures(paths)
    compass, _ = research_compass.build_compass(now="2026-08-13T00:00:00+00:00")
    card = next(x for x in compass["important_discoveries"] if x["kind"] == "local_vortex_energy_dataset")
    assert card["pair_charge_patterns"]["+-"] == 29
    assert card["energy_peak_before_geometry_collapse"] == 0
    assert "binding_energy" in card["not_claimed"]


def test_run_writes_root_compass_report_and_memory(monkeypatch, tmp_path):
    paths = _install_paths(monkeypatch, tmp_path)
    _fixtures(paths)
    research_compass.run(persist=True)
    assert paths["_REPORT_JSON"].exists()
    assert paths["_REPORT_MD"].exists()
    assert paths["_ROOT_MD"].exists()
    assert paths["_MEMORY"].exists()
    assert "大事な発見・進展" in paths["_ROOT_MD"].read_text()
    memory = json.loads(paths["_MEMORY"].read_text())
    assert memory["policy"]["raw_evidence_deleted"] is False
