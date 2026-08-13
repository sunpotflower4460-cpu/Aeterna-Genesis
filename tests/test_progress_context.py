from ai_lab.dream import progress_context
from ai_lab.dream import progress_ratchet


KNOBS = {
    "noise_amplitude": 4e-5,
    "correlation_length": 3.0,
    "diffusion_ratio": 0.4,
    "drive_strength": 2.0,
    "quench_duration": 8.0,
}


def _ranked(pid: str = "X-a", *, family: str = "white", knobs=None):
    return {
        "pattern_id": pid,
        "score": 2.0,
        "specificity": 0.8,
        "exact_rate": 0.7,
        "nearby_rate": 0.5,
        "contrast_rate": 0.0,
        "recent_studies": 0,
        "status": "REPEATED_SPECIFIC_CANDIDATE",
        "search_focus": {"family": family, "knobs": dict(knobs or KNOBS)},
        "row": {},
    }


def test_same_pid_and_executed_value_but_different_family_are_different_questions():
    a = progress_context._x_question_key("X-a", "white", KNOBS, "drive_strength", 1.5)
    b = progress_context._x_question_key("X-a", "single_seed", KNOBS, "drive_strength", 1.5)
    assert a != b
    assert "ctx:" in a and "ctx:" in b


def test_same_pid_and_executed_value_but_different_other_base_knob_are_different_questions():
    changed = dict(KNOBS)
    changed["correlation_length"] = 5.0
    a = progress_context._x_question_key("X-a", "white", KNOBS, "drive_strength", 1.5)
    b = progress_context._x_question_key("X-a", "white", changed, "drive_strength", 1.5)
    assert a != b


def test_identical_full_start_context_is_canonical_and_order_independent():
    reversed_knobs = dict(reversed(list(KNOBS.items())))
    assert progress_context.context_signature("white", KNOBS) == progress_context.context_signature(
        "white", reversed_knobs
    )
    assert progress_context._x_question_key(
        "X-a", "white", KNOBS, "drive_strength", 1.5
    ) == progress_context._x_question_key(
        "X-a", "white", reversed_knobs, "drive_strength", 1.5
    )


def test_context_identity_contains_start_side_only_not_outcome_fields():
    context = progress_context._canonical_context("white", KNOBS)
    assert set(context) == {"version", "family", "base_knobs"}
    serialized = repr(context)
    for forbidden in (
        "same_pattern_seen", "hit", "episode", "morphology", "geometry", "energy", "split"
    ):
        assert forbidden not in serialized


def test_legacy_contextless_question_does_not_suppress_new_context_coverage():
    cells = progress_context._x_candidate_cells(
        pattern_id="X-a", family="white", knobs=KNOBS, burst_id="coverage"
    )
    assert cells
    cell = cells[0]
    legacy = progress_ratchet._question_key(
        "x", "X-a", cell["knob"], cell["executed_value"]
    )
    old_only = progress_context._x_coverage("X-a", "white", KNOBS, counts={legacy: 3})
    assert old_only["seen"] == 0
    assert old_only["legacy_contextless_keys_count_as_seen"] is False

    new_key = str(cell["progress_question_key"])
    current = progress_context._x_coverage("X-a", "white", KNOBS, counts={new_key: 1})
    assert current["seen"] == 1


def test_legacy_pattern_wide_escape_remains_compatible(monkeypatch):
    history = [{
        "progress": {
            "next_burst_escape_required": True,
            "next_burst_escape_targets": ["x:X-a"],
        }
    }]
    monkeypatch.setattr(progress_ratchet, "_full_history", lambda: history)
    monkeypatch.setattr(progress_ratchet, "_memory", lambda: {"entries": []})
    monkeypatch.setattr(
        progress_ratchet,
        "_durable_question_counts",
        lambda **kwargs: {},
    )
    monkeypatch.setattr(
        progress_context,
        "_V10_RANK_X",
        lambda limit, history: [_ranked()],
    )
    assert progress_context.rank_x_focuses(limit=1, history=history) == []


def test_context_escape_blocks_only_same_context(monkeypatch):
    blocked = progress_context._x_escape_target("X-a", "white", KNOBS)
    history = [{
        "progress": {
            "next_burst_escape_required": True,
            "next_burst_escape_targets": [blocked],
        }
    }]
    monkeypatch.setattr(progress_ratchet, "_full_history", lambda: history)
    monkeypatch.setattr(progress_ratchet, "_memory", lambda: {"entries": []})
    monkeypatch.setattr(
        progress_ratchet,
        "_durable_question_counts",
        lambda **kwargs: {},
    )

    monkeypatch.setattr(
        progress_context,
        "_V10_RANK_X",
        lambda limit, history: [_ranked()],
    )
    assert progress_context.rank_x_focuses(limit=1, history=history) == []

    changed = dict(KNOBS)
    changed["correlation_length"] = 5.0
    monkeypatch.setattr(
        progress_context,
        "_V10_RANK_X",
        lambda limit, history: [_ranked(knobs=changed)],
    )
    reopened = progress_context.rank_x_focuses(limit=1, history=history)
    assert len(reopened) == 1
    assert reopened[0]["pattern_id"] == "X-a"
    assert reopened[0]["escape_target"] != blocked


def test_ordered_x_specs_write_contextual_question_keys(monkeypatch):
    monkeypatch.setattr(progress_ratchet, "_durable_question_counts", lambda **kwargs: {})
    specs = progress_context._ordered_specs(
        lane="x", target="X-a", family="white", knobs=KNOBS,
        burst_id="dream-test", budget=4,
    )
    assert len(specs) == 4
    assert specs[0]["progress_question_key"] is None
    assert specs[1]["progress_question_key"] is None
    interventions = specs[2:]
    assert interventions
    assert all("|ctx:" in str(row["progress_question_key"]) for row in interventions)
    assert all(row["progress_context_signature"] for row in interventions)
