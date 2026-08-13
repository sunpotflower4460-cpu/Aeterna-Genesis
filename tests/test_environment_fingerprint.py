import json

from ai_lab.dream import environment_fingerprint


def test_environment_fingerprint_records_versions_and_contract_hashes(monkeypatch, tmp_path):
    easy = tmp_path / "easy.json"
    out = tmp_path / "environment.json"
    requirements = tmp_path / "requirements.txt"
    workflow = tmp_path / "dream-loop.yml"
    easy.write_text(json.dumps({"burst_id": "dream-test"}))
    requirements.write_text("numpy>=1.24\n")
    workflow.write_text("name: test\n")
    monkeypatch.setattr(environment_fingerprint, "_EASY", easy)
    monkeypatch.setattr(environment_fingerprint, "_OUTPUT", out)
    monkeypatch.setattr(environment_fingerprint, "_REQUIREMENTS", requirements)
    monkeypatch.setattr(environment_fingerprint, "_DREAM_WORKFLOW", workflow)
    report = environment_fingerprint.run(persist=True)
    assert report["burst_id"] == "dream-test"
    assert report["python"]["version_info"]
    assert isinstance(report["installed_distributions"], dict)
    assert report["contracts"]["requirements_txt_sha256"]
    assert report["contracts"]["dream_loop_workflow_sha256"]
    assert report["semantics"]["matching_environment_proves_scientific_claim"] is False
    assert report["integrity"]["changes_scientific_truth_gate"] is False
    assert json.loads(out.read_text())["burst_id"] == "dream-test"


def test_environment_fingerprint_never_captures_arbitrary_environment_variables(monkeypatch, tmp_path):
    easy = tmp_path / "easy.json"
    easy.write_text(json.dumps({"burst_id": "dream-test"}))
    monkeypatch.setattr(environment_fingerprint, "_EASY", easy)
    monkeypatch.setattr(environment_fingerprint, "_REQUIREMENTS", tmp_path / "missing-req")
    monkeypatch.setattr(environment_fingerprint, "_DREAM_WORKFLOW", tmp_path / "missing-workflow")
    monkeypatch.setenv("AETERNA_FAKE_SECRET", "do-not-record")
    report = environment_fingerprint.build_fingerprint()
    text = json.dumps(report)
    assert "AETERNA_FAKE_SECRET" not in text
    assert "do-not-record" not in text
    assert set(report["numerical_thread_environment"]) == set(environment_fingerprint._NUMERICAL_ENV_NAMES)
