from ai_lab.aquarium.compass import build_compass


def test_compass_keeps_intent_out_of_science_and_compute():
    compass = build_compass()
    policy = compass["policy"]
    assert policy["planning_only"] is True
    assert policy["intent_is_scientific_evidence"] is False
    assert policy["notes_are_scientific_evidence"] is False
    assert policy["changes_physics"] is False
    assert policy["changes_initial_conditions"] is False
    assert policy["routes_physical_compute"] is False
    assert policy["changes_scientific_truth_gate"] is False
    assert policy["promotes_rooms"] is False
    assert policy["changes_official_levels"] is False


def test_compass_links_backlog_instruments_without_promoting_them():
    compass = build_compass()
    by_id = {a["aquarium_id"]: a for a in compass["aquaria"]}
    metric = by_id["AQ-METRIC-001"]
    assert "metric-from-relations" in metric["requested_instruments"]
    assert any(i["request_id"] == "metric-from-relations" for i in metric["open_instruments"])


def test_compass_preserves_human_and_ai_notes_together():
    compass = build_compass()
    by_id = {a["aquarium_id"]: a for a in compass["aquaria"]}
    division = by_id["AQ-DIV-001"]
    assert division["notes"]["latest_human_note"]
    assert division["notes"]["latest_ai_direction"]
