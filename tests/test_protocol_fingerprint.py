from ai_lab.dream import protocol_fingerprint


def test_protocol_fingerprint_is_canonical_for_same_parsed_options():
    a = protocol_fingerprint.build_protocol(
        burst_id="dream-test",
        argv=["--quick", "--trials", "8", "--workers", "1", "--seed", "7"],
    )
    b = protocol_fingerprint.build_protocol(
        burst_id="dream-test",
        argv=["--workers", "1", "--seed", "7", "--trials", "8", "--quick"],
    )
    assert a["protocol_sha256"] == b["protocol_sha256"]
    assert a["parsed_config"] == b["parsed_config"]
    assert a["capture_policy"]["raw_shell_argv_recorded"] is False
    assert a["capture_policy"]["arbitrary_environment_recorded"] is False
    assert a["semantics"]["protocol_hash_proves_scientific_claim"] is False


def test_protocol_fingerprint_changes_when_research_budget_changes():
    a = protocol_fingerprint.build_protocol(
        burst_id="dream-test", argv=["--quick", "--trials", "8", "--seed", "7"]
    )
    b = protocol_fingerprint.build_protocol(
        burst_id="dream-test", argv=["--quick", "--trials", "9", "--seed", "7"]
    )
    assert a["protocol_sha256"] != b["protocol_sha256"]
    assert a["parsed_config"]["trials"] == 8
    assert b["parsed_config"]["trials"] == 9
