import json

from ai_lab.dream import runtime_context_audit


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _fixtures(tmp_path):
    easy = tmp_path / "easy.json"
    environment = tmp_path / "environment.json"
    protocol = tmp_path / "protocol.json"
    _write(easy, {"burst_id": "dream-test"})
    _write(environment, {
        "burst_id": "dream-test",
        "contracts": {"requirements_txt_sha256": "r", "dream_loop_workflow_sha256": "w"},
        "semantics": {"captures_secrets": False},
    })
    _write(protocol, {
        "burst_id": "dream-test",
        "protocol_sha256": "p",
        "capture_policy": {
            "recognized_parser_options_only": True,
            "raw_shell_argv_recorded": False,
            "arbitrary_environment_recorded": False,
        },
    })
    return easy, environment, protocol


def test_matching_runtime_context_is_valid(tmp_path):
    easy, environment, protocol = _fixtures(tmp_path)
    report = runtime_context_audit.build_audit(
        easy_path=easy, environment_path=environment, protocol_path=protocol
    )
    assert report["valid"] is True
    assert report["errors"] == []
    assert report["integrity"]["runtime_context_is_scientific_evidence"] is False


def test_stale_environment_or_protocol_is_rejected(tmp_path):
    easy, environment, protocol = _fixtures(tmp_path)
    env = json.loads(environment.read_text())
    env["burst_id"] = "old-env"
    _write(environment, env)
    pro = json.loads(protocol.read_text())
    pro["burst_id"] = "old-protocol"
    _write(protocol, pro)
    report = runtime_context_audit.build_audit(
        easy_path=easy, environment_path=environment, protocol_path=protocol
    )
    assert report["valid"] is False
    assert any("environment burst mismatch" in x for x in report["errors"])
    assert any("protocol burst mismatch" in x for x in report["errors"])


def test_missing_or_malformed_context_fails_closed(tmp_path):
    easy, environment, protocol = _fixtures(tmp_path)
    protocol.unlink()
    environment.write_text("{bad-json")
    report = runtime_context_audit.build_audit(
        easy_path=easy, environment_path=environment, protocol_path=protocol
    )
    assert report["valid"] is False
    assert any("execution environment is unreadable or malformed" in x for x in report["errors"])
    assert any("parsed research protocol is missing" in x for x in report["errors"])


def test_protocol_capture_boundary_fails_closed(tmp_path):
    easy, environment, protocol = _fixtures(tmp_path)
    pro = json.loads(protocol.read_text())
    pro["capture_policy"]["raw_shell_argv_recorded"] = True
    pro["capture_policy"]["recognized_parser_options_only"] = False
    _write(protocol, pro)
    report = runtime_context_audit.build_audit(
        easy_path=easy, environment_path=environment, protocol_path=protocol
    )
    assert report["valid"] is False
    assert any("recognized parser options only" in x for x in report["errors"])
    assert any("must not persist raw shell argv" in x for x in report["errors"])
