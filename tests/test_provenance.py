"""Foundation language: Genesis Provenance / Causal Closure / multi-axis capability + per-capability
seeded flags. These extend (do NOT replace) ANTI_DRIFT: they make "where did that part come from?" a
recorded structure. no_touch: measures.py and rooms/official/ are read-only here.
"""

import json
import pathlib

import jsonschema
import yaml

from genesis.diagnostics import higher_levels as hl

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_individuality_records_per_capability_seeded_localization():
    """SH places one bump -> localization is SEEDED while self-repair/persistence are EMERGENT (GPT②).
    The measure records this per-capability instead of claiming 'individuality emerged from 0'."""
    # localization seeded (SH): still L4 (robustness emergent) but flagged seeded_localization
    lvl, det, mb = hl.assess_individuality_level(
        amax=1.41, area_fraction=0.015, persistence_change=2e-8, recovers_after_perturbation=True,
        size_independent=True, centroid_drift=0.0, localization_seeded=True)
    assert lvl == 4
    assert det["seeded_localization"] is True and det["emerged_self_repair"] is True
    assert det["emerged_persistence"] is True and det["emerged_size_independence"] is True
    assert "localization SEEDED" in mb["emergent_ceiling"]
    # default: not flagged (back-compatible)
    _, det0, mb0 = hl.assess_individuality_level(1.41, 0.015, 2e-8, True, True, 0.0)
    assert det0["seeded_localization"] is False and mb0["seeded_localization"] is False


def test_replication_records_seeded_founders_and_event_not_commanded():
    """Gray-Scott: the division EVENT is emergent (not commanded), but the population grows from SEEDED
    founders -> not '0 -> L7'. New honest flags are additive; the old key stays for back-compat."""
    _, det, _ = hl.assess_replication_level([8, 12, 18, 20])
    assert det["division_event_not_commanded"] is True
    assert det["spot_count_growth_from_seeded_founders"] is True
    assert det["division_not_seeded"] is True                # back-compat key preserved
    assert det["full_l7_emergence"] is False


def test_provenance_schemas_are_valid_and_enforce_claim_excludes():
    """The three new schemas parse as valid JSON-Schema, and an environmental_condition entry MUST carry
    claim_excludes (you cannot claim an imposed environment is emergent)."""
    for name in ("provenance", "preparation", "causal-ancestry"):
        schema = json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
    prov = json.loads((ROOT / "schemas" / "provenance.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(prov)
    # emerged_state that is manually_set -> invalid (only born-from-development may be emerged)
    bad = {"schema_version": 1, "entries": [
        {"name": "vortices", "input_class": "emerged_state", "manually_set": True, "outcome_targeted": False}]}
    assert not validator.is_valid(bad)
    # environmental_condition WITHOUT claim_excludes -> invalid
    bad2 = {"schema_version": 1, "entries": [
        {"name": "dT", "input_class": "environmental_condition", "manually_set": True, "outcome_targeted": False}]}
    assert not validator.is_valid(bad2)
    # a clean example validates
    good = {"schema_version": 1, "entries": [
        {"name": "psi", "input_class": "prepared_state", "manually_set": False, "source": "preparation_result",
         "outcome_targeted": False},
        {"name": "temperature_gradient", "input_class": "environmental_condition", "manually_set": True,
         "outcome_targeted": False, "claim_excludes": ["spontaneous_temperature_gradient"]},
        {"name": "convection_rolls", "input_class": "emerged_state", "manually_set": False, "outcome_targeted": False}]}
    validator.validate(good)


def test_causal_closure_audit_matches_existing_rooms():
    """The CAUSAL_CLOSURE audit table must reflect the ACTUAL existing Rooms (no_touch: read-only). g002 is
    externally_driven (imposed ΔT), g003 is autonomous, g001 is a time-programmed quench -- all C1 today."""
    drive = {}
    for room in ("room-g001-a", "room-g002-a", "room-g003-a"):
        g = yaml.safe_load((ROOT / "rooms" / "official" / room / "genesis.yaml").read_text())
        drive[room] = g.get("drive_class")
    assert drive["room-g002-a"] == "externally_driven"          # imposed temperature difference
    assert drive["room-g003-a"] == "autonomous"                 # no imposed environment (closest to C2)
    assert drive["room-g001-a"] == "time_programmed_environment"  # quench is a scripted time-environment
    audit = (ROOT / "docs" / "CAUSAL_CLOSURE.md").read_text()
    assert "room-g002-a" in audit and "spontaneous_temperature_gradient" in audit  # env labeled with claim_excludes
