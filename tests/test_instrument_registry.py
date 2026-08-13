from ai_lab.dream import instrument_registry


KNOWN = [
    "metric-from-relations",
    "identity-continuity",
    "damage-recovery",
    "growth-accounting",
    "predictive-holdout",
    "lineage-accounting",
]


def _request(rid: str, **overrides):
    row = {
        "id": rid,
        "question": "measure something",
        "purpose": "instrument only",
        "new_physical_axiom": False,
        "target_morphology_seeded": False,
        "may_use_scaffolded_analogy_lane": True,
        "scaffolded_lane_cannot_count_as_pure_genesis_proof": True,
    }
    row.update(overrides)
    return row


def test_all_current_instruments_have_nonempty_claim_safe_contracts():
    assert sorted(instrument_registry.INSTRUMENTS) == sorted(KNOWN)
    for rid in KNOWN:
        row = instrument_registry.get(rid)
        assert row is not None
        assert row["capability"]
        assert row["implementation_contract"]
        assert row["required_controls"]
        assert row["claim_blocks"]
        assert row["scaffolded_parallel_lane_is_pure_genesis_proof"] is False


def test_unknown_instrument_fails_closed():
    errors = instrument_registry.validate_request(_request("mystery-instrument"))
    assert any("unregistered instrument id" in error for error in errors)


def test_target_morphology_or_new_axiom_is_rejected():
    assert any(
        "target morphology" in error
        for error in instrument_registry.validate_request(
            _request("identity-continuity", target_morphology_seeded=True)
        )
    )
    assert any(
        "new physical axiom" in error
        for error in instrument_registry.validate_request(
            _request("identity-continuity", new_physical_axiom=True)
        )
    )


def test_scaffolded_lane_must_remain_explicitly_non_proof():
    errors = instrument_registry.validate_request(
        _request(
            "growth-accounting",
            may_use_scaffolded_analogy_lane=True,
            scaffolded_lane_cannot_count_as_pure_genesis_proof=False,
        )
    )
    assert any("lacks explicit non-proof boundary" in error for error in errors)


def test_frontier_duplicate_instrument_ids_fail_contract():
    report = instrument_registry.validate_frontier_requests({
        "instrument_requests": [
            _request("identity-continuity"),
            _request("identity-continuity"),
        ]
    })
    assert report["valid"] is False
    assert any("duplicate instrument request id" in error for error in report["errors"])
    assert report["request_is_evidence_of_phenomenon"] is False
