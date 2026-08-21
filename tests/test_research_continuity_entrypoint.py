from __future__ import annotations

from copy import deepcopy

from ai_lab.dream import research_continuity_entrypoint as entrypoint


def _lesson(*, key: str, lane: str, kind: str, priority: int, snapshot: dict | None = None) -> dict:
    return {
        "key": key,
        "lane": lane,
        "kind": kind,
        "priority": priority,
        "importance": "carry",
        "snapshot": snapshot or {},
        "source": f"source:{key}",
        "last_seen_at": "2026-08-21T00:00:00Z",
    }


def test_balanced_handoff_prevents_deep_time_from_crowding_everything_out() -> None:
    lessons: list[dict] = []

    for i in range(20):
        lessons.append(_lesson(
            key=f"deep:{i:02d}",
            lane="strict-deep-time",
            kind="deep_time",
            priority=99 - i,
            snapshot={
                "candidate_id": f"deep-{i:02d}",
                "effective_F_depth": 7 if i < 2 else 6,
                "prefix_identity": "MATCH",
                "long_lived": i == 2,
                "transition_seen": i < 4,
                "scientific_usable": True,
            },
        ))

    for i in range(10):
        lessons.append(_lesson(
            key=f"x:X-{i:02d}",
            lane="strict/open-ended-followup",
            kind="unknown_transition",
            priority=80 - i,
            snapshot={
                "pattern_id": f"X-{i:02d}",
                "status": "REPEATED_SPECIFIC_CANDIDATE" if i < 3 else "WEAKENED",
                "exact_rate": 0.8,
                "nearby_rate": 0.2,
                "contrast_rate": 0.0,
            },
        ))

    lessons += [
        _lesson(
            key="geometry:triangle-vs-control-separation",
            lane="strict-geometry",
            kind="competing_geometry_explanation",
            priority=90,
            snapshot={
                "triangle_rate": 0.4,
                "control_rate": 0.8,
                "triangle_excess_rate": -0.4,
                "triangle_required": False,
            },
        ),
        _lesson(
            key="energy:vertex-asymmetry-vs-geometry",
            lane="strict-local-energy",
            kind="local_energy_competing_explanation",
            priority=90,
            snapshot={
                "pair_relations": 30,
                "pair_only": 20,
                "triad_energy_relations": 18,
                "split_asymmetry": 0.1,
                "no_split_asymmetry": 0.2,
                "energy_peak_preceded_geometry": 0,
            },
        ),
        _lesson(
            key="free:fast_quench",
            lane="free-hypothesis",
            kind="exploratory_mechanism_question",
            priority=72,
            snapshot={"strict_transfer_question": "Can quench-rate sensitivity survive strict-zero retesting?"},
        ),
        _lesson(
            key="science:doi:turing",
            lane="science-bridge",
            kind="external_scientific_context",
            priority=70,
            snapshot={
                "title": "The Chemical Basis of Morphogenesis",
                "doi": "10.1098/rstb.1952.0012",
                "mechanism": "spatial instability",
            },
        ),
        _lesson(
            key="crossworld:shadow-semantics",
            lane="cross-world-shadow",
            kind="cross_world_integrity",
            priority=86,
        ),
        _lesson(
            key="ops:instrument:identity-continuity",
            lane="research-operations",
            kind="operational_or_instrument_debt",
            priority=82,
            snapshot={"question": "Can persistent identity be measured without using the target outcome?"},
        ),
    ]

    science_directions = {
        "directions": [
            {
                "id": f"science-direction-{i}",
                "enabled": True,
                "question": f"Literature-inspired question {i}",
                "strict_transfer_question": f"Strict transfer {i}",
                "source_reference": {"doi": f"10.example/{i}"},
            }
            for i in range(4)
        ]
    }

    original = deepcopy(lessons)
    carry = entrypoint.balanced_carry_forward(lessons, science_directions)

    assert len(carry) <= 40
    assert lessons == original  # selection must not mutate/delete the complete lesson ledger

    counts: dict[str, int] = {}
    for row in carry:
        counts[row["lane"]] = counts.get(row["lane"], 0) + 1
        assert row.get("question_or_lesson")

    assert counts.get("strict-deep-time", 0) <= 6
    assert counts.get("strict/open-ended-followup", 0) <= 8
    assert counts.get("strict-geometry", 0) >= 1
    assert counts.get("strict-local-energy", 0) >= 1
    assert counts.get("free-hypothesis", 0) >= 1
    assert counts.get("science-bridge", 0) >= 1
    assert counts.get("cross-world-shadow", 0) >= 1
    assert counts.get("research-operations", 0) >= 1

    science_rows = [row for row in carry if row.get("lane") == "science-bridge/free-hypothesis"]
    assert len(science_rows) == 4
    assert all(row["counts_as_strict_zero_evidence"] is False for row in science_rows)


def test_science_direction_reservation_is_capped() -> None:
    directions = {
        "directions": [
            {
                "id": f"paper-{i}",
                "enabled": True,
                "question": f"Question {i}",
                "strict_transfer_question": f"Transfer {i}",
                "source_reference": {"doi": f"10.test/{i}"},
            }
            for i in range(20)
        ]
    }
    carry = entrypoint.balanced_carry_forward([], directions)
    assert len(carry) == entrypoint._SCIENCE_DIRECTION_QUOTA
    assert all(row["counts_as_strict_zero_evidence"] is False for row in carry)


def test_unknown_future_lane_gets_small_reserve_without_breaking_maximum() -> None:
    lessons = [
        _lesson(
            key=f"future:{i}",
            lane="future-new-lane",
            kind="future_kind",
            priority=100 - i,
            snapshot={"question": f"future question {i}"},
        )
        for i in range(12)
    ]
    carry = entrypoint.balanced_carry_forward(lessons, {"directions": []})
    assert len(carry) == entrypoint._OTHER_LANES_QUOTA
    assert all(row["lane"] == "future-new-lane" for row in carry)
    assert all(row["question_or_lesson"] for row in carry)
