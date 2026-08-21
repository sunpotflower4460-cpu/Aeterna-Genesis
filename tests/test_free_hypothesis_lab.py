from __future__ import annotations

from ai_lab.dream import free_hypothesis_lab as lab


def test_direction_and_auto_hypotheses_remain_exploratory_only() -> None:
    rows = lab.propose_hypotheses(max_hypotheses=8)
    assert rows
    assert any(h.experiment_type == "circular_confinement" for h in rows)
    assert any(h.experiment_type == "annular_energy_shell" for h in rows)
    for h in rows:
        assert h.provenance_class != "STRICT_ZERO"
        assert h.abstract_factor
        assert h.strict_transfer_question


def test_free_lab_runs_real_interventions_but_never_returns_strict_evidence() -> None:
    report = lab.run(max_hypotheses=2, replicates=1, seed=123, quick=True, persist=False)
    assert report["mode"] == "free-hypothesis-exploratory-sandbox"
    assert len(report["hypotheses"]) == 2
    assert report["strict_bridge"]["strict_zero_evidence_incremented"] is False
    assert report["strict_bridge"]["room_promotion_allowed"] is False
    assert report["honesty"]["free_lab_is_pure_genesis"] is False
    for row in report["hypotheses"]:
        assert row["counts_as_strict_zero_evidence"] is False
        assert row["may_change_room_or_official_level"] is False
        assert row["may_seed_new_strict_target"] is False
        assert row["runs"]


def test_free_lab_is_deterministic_for_same_seed_and_inputs() -> None:
    a = lab.run(max_hypotheses=1, replicates=1, seed=987, quick=True, persist=False)
    b = lab.run(max_hypotheses=1, replicates=1, seed=987, quick=True, persist=False)
    ar = a["hypotheses"][0]["runs"][0]
    br = b["hypotheses"][0]["runs"][0]
    assert ar["finite"] == br["finite"]
    assert ar.get("checksum") == br.get("checksum")


def test_scaffolded_geometry_is_explicitly_not_emergent_geometry() -> None:
    rows = lab.propose_hypotheses(max_hypotheses=10)
    geometry = [h for h in rows if "GEOMETRY_SCAFFOLDED" in h.provenance_class]
    assert geometry
    for h in geometry:
        assert "形" not in h.strict_transfer_question or "置かず" in h.strict_transfer_question
