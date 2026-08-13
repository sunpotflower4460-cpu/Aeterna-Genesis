from pathlib import Path

from ai_lab.dream import production_protocol


def _workflow(tmp_path: Path, command: str) -> Path:
    path = tmp_path / "dream-loop.yml"
    path.write_text(
        "name: Genesis Dream Loop\n"
        "jobs:\n"
        "  research-burst:\n"
        "    steps:\n"
        f"      - name: {production_protocol._TARGET_STEP}\n"
        "        run: |\n"
        + "\n".join(f"          {line}" for line in command.splitlines())
        + "\n"
    )
    return path


def _full_command(**overrides):
    values = {
        "trials": 8,
        "native3d_trials": 2,
        "followup_trials_2d": 4,
        "fission_path_trials_2d": 2,
        "deep_time_max_leads": 1,
        "open_ended_probes": 4,
        "unknown_followup_max_patterns": 1,
        "root_law_trials": 6,
        "frontier_experiments": 6,
    }
    values.update(overrides)
    return f"""python -m ai_lab.dream.strict_goal_loop \\
--quick \\
--trials {values['trials']} \\
--native3d-trials {values['native3d_trials']} \\
--followup-trials-2d {values['followup_trials_2d']} \\
--fission-path-trials-2d {values['fission_path_trials_2d']} \\
--deep-time-max-leads {values['deep_time_max_leads']} \\
--open-ended-probes {values['open_ended_probes']} \\
--unknown-followup-max-patterns {values['unknown_followup_max_patterns']} \\
--root-law-trials {values['root_law_trials']} \\
--frontier-experiments {values['frontier_experiments']}"""


def test_production_protocol_extracts_and_parses_multiline_command(tmp_path, monkeypatch):
    path = _workflow(tmp_path, _full_command())
    monkeypatch.setattr(production_protocol, "_REPO", tmp_path)
    report = production_protocol.build_contract(path)
    assert report["valid"] is True
    assert report["parsed_config"]["trials"] == 8
    assert report["parsed_config"]["open_ended_probes"] == 4
    assert report["disabled_required_lanes"] == []
    assert report["semantics"]["required_lane_means_scientific_success_required"] is False


def test_zeroed_required_lane_fails_configuration_contract(tmp_path, monkeypatch):
    path = _workflow(tmp_path, _full_command(open_ended_probes=0))
    monkeypatch.setattr(production_protocol, "_REPO", tmp_path)
    report = production_protocol.build_contract(path)
    assert report["valid"] is False
    assert any(row["option"] == "open_ended_probes" for row in report["disabled_required_lanes"])


def test_no_record_is_rejected_for_production_protocol(tmp_path, monkeypatch):
    path = _workflow(tmp_path, _full_command() + " --no-record")
    monkeypatch.setattr(production_protocol, "_REPO", tmp_path)
    report = production_protocol.build_contract(path)
    assert report["valid"] is False
    assert any("--no-record" in error for error in report["errors"])
