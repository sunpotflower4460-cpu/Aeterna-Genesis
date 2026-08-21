from __future__ import annotations

from ai_lab.dream import research_continuity_entrypoint as continuity


def _lesson(key: str, lane: str, kind: str, priority: int, snapshot: dict | None = None) -> dict:
    return {
        "key": key,
        "lane": lane,
        "kind": kind,
        "priority": priority,
        "importance": "carry",
        "snapshot": snapshot or {},
        "source": "test",
        "last_seen_at": "2026-01-01T00:00:00Z",
    }


def test_deep_time_cannot_monopolize_working_handoff() -> None:
    lessons = [
        _lesson(
            f"deep:{i}",
            "strict-deep-time",
            "deep_time",
            88,
            {
                "candidate_id": f"deep-{i}",
                "status": "TRANSITION_SEEN_VERIFYING",
                "effective_F_depth": 6,
                "prefix_identity": "MATCH",
                "long_lived": False,
                "transition_seen": True,
            },
        )
        for i in range(24)
    ]
    lessons += [
        _lesson("geometry", "strict-geometry", "competing_geometry_explanation", 90, {
            "triangle_seen": 5,
            "triangle_split": 2,
            "control_seen": 18,
            "control_split": 16,
            "triangle_required": False,
        }),
        _lesson("energy", "strict-local-energy", "local_energy_competing_explanation", 90, {
            "pair_relations": 30,
            "pair_only": 25,
            "triad_energy_relations": 20,
            "energy_peak_preceded_geometry": 0,
        }),
    ]
    lessons += [
        _lesson(f"x:{i}", "strict/open-ended-followup", "unknown_transition", 80, {
            "pattern_id": f"X-{i}",
            "status": "REPEATED_SPECIFIC_CANDIDATE",
            "exact": {"hit": 10, "n": 12},
            "nearby": {"hit": 2, "n": 12},
            "contrast": {"hit": 0, "n": 12},
        })
        for i in range(8)
    ]
    lessons += [
        _lesson(f"free:{i}", "free-hypothesis", "exploratory_mechanism_question", 72, {
            "strict_transfer_question": f"strict retest {i}",
        })
        for i in range(5)
    ]
    lessons += [
        _lesson(f"ops:{i}", "research-operations", "operational_or_instrument_debt", 82, {
            "question": f"instrument question {i}",
        })
        for i in range(6)
    ]
    lessons += [
        _lesson("cw", "cross-world-shadow", "cross_world_integrity", 86)
    ]
    science = {
        "directions": [
            {
                "id": f"science-{i}",
                "enabled": True,
                "question": f"science question {i}",
                "strict_transfer_question": f"science strict retest {i}",
                "source_reference": {"doi": f"10.0/{i}"},
            }
            for i in range(4)
        ]
    }

    rows = continuity.diverse_carry_forward(lessons, science, limit=40)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["handoff_bucket"]] = counts.get(row["handoff_bucket"], 0) + 1

    assert len(rows) <= 40
    assert counts["strict-deep-time"] <= continuity._BUCKET_CAPS["strict-deep-time"]
    assert counts["strict-deep-time"] >= continuity._BUCKET_MINIMUMS["strict-deep-time"]
    assert counts["unknown-x"] >= 4
    assert counts["science-bridge"] >= 4
    assert counts["free-hypothesis"] >= 2
    assert counts["research-operations"] >= 4
    assert counts["strict-geometry"] >= 1
    assert counts["strict-local-energy"] >= 1
    assert counts["cross-world"] >= 1


def test_actionable_handoff_text_is_not_null_for_core_lanes() -> None:
    lessons = [
        _lesson("geometry", "strict-geometry", "competing_geometry_explanation", 90, {
            "triangle_seen": 5,
            "triangle_split": 2,
            "control_seen": 18,
            "control_split": 16,
            "triangle_required": False,
        }),
        _lesson("energy", "strict-local-energy", "local_energy_competing_explanation", 90, {
            "pair_relations": 30,
            "pair_only": 25,
            "triad_energy_relations": 20,
            "split_asymmetry": 0.08,
            "no_split_asymmetry": 0.10,
            "energy_peak_preceded_geometry": 0,
        }),
        _lesson("x:X-a", "strict/open-ended-followup", "unknown_transition", 80, {
            "pattern_id": "X-a",
            "status": "WEAKENED",
            "exact": {"hit": 1, "n": 3},
            "nearby": {"hit": 0, "n": 3},
            "contrast": {"hit": 0, "n": 3},
        }),
        _lesson("deep:a", "strict-deep-time", "deep_time", 88, {
            "candidate_id": "deep-a",
            "status": "STABLE_THROUGH_64TAU",
            "effective_F_depth": 4,
            "prefix_identity": "MATCH",
            "long_lived": True,
            "transition_seen": False,
        }),
        _lesson("cross", "cross-world-shadow", "cross_world_integrity", 86),
    ]
    rows = continuity.diverse_carry_forward(lessons, {"directions": []}, limit=40)
    assert rows
    assert all(isinstance(row.get("question_or_lesson"), str) and row["question_or_lesson"].strip() for row in rows)
    by_kind = {row["kind"]: row for row in rows}
    assert "三角形" in by_kind["competing_geometry_explanation"]["question_or_lesson"]
    assert "因果" in by_kind["local_energy_competing_explanation"]["question_or_lesson"]
    assert "何を変えると消える" in by_kind["unknown_transition"]["question_or_lesson"]
    assert "raw depth" in by_kind["deep_time"]["question_or_lesson"]
    assert "同じ物理" in by_kind["cross_world_integrity"]["question_or_lesson"]


def test_science_direction_stays_non_strict_and_gets_science_bucket() -> None:
    rows = continuity.diverse_carry_forward([], {
        "directions": [{
            "id": "paper-a",
            "enabled": True,
            "question": "Does a literature-inspired timescale change the response?",
            "strict_transfer_question": "Retest the timescale from strict zero.",
            "source_reference": {"doi": "10.1/example"},
        }]
    })
    assert len(rows) == 1
    row = rows[0]
    assert row["handoff_bucket"] == "science-bridge"
    assert row["counts_as_strict_zero_evidence"] is False
    assert row["strict_transfer_question"] == "Retest the timescale from strict zero."


def test_full_lessons_are_not_truncated_by_handoff_caps() -> None:
    lessons = [
        _lesson(f"deep:{i}", "strict-deep-time", "deep_time", 88, {
            "candidate_id": f"deep-{i}",
            "effective_F_depth": 6,
            "prefix_identity": "MATCH",
        })
        for i in range(20)
    ]
    selected = continuity.diverse_carry_forward(lessons, {"directions": []}, limit=40)
    assert len(lessons) == 20
    assert len(selected) == continuity._BUCKET_CAPS["strict-deep-time"]
    # The selector returns a compact navigation view only; source lesson objects are untouched.
    assert all("selection_reason" not in row for row in lessons)
