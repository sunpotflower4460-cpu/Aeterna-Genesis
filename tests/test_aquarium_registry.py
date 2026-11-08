import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_aquarium_registry_schema_and_unique_ids():
    schema = load_json("schemas/aquarium-registry.schema.json")
    doc = load_json("aquaria/registry.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(doc)

    ids = [a["aquarium_id"] for a in doc["aquaria"]]
    assert len(ids) == len(set(ids))


def test_aquarium_notebook_schema_and_references():
    schema = load_json("schemas/aquarium-notebook.schema.json")
    notebook = load_json("aquaria/notebook.json")
    registry = load_json("aquaria/registry.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(notebook)

    aquarium_ids = {a["aquarium_id"] for a in registry["aquaria"]}
    note_ids = [n["note_id"] for n in notebook["entries"]]
    assert len(note_ids) == len(set(note_ids))
    assert all(n["aquarium_id"] in aquarium_ids for n in notebook["entries"])


def test_intent_is_planning_only_and_cannot_promote_science():
    doc = load_json("aquaria/registry.json")
    policy = doc["policy"]
    assert policy["intent_is_scientific_evidence"] is False
    assert policy["planning_may_read_intent"] is True
    assert policy["physics_may_read_intent_text"] is False
    assert policy["goal_directed_equals_target_encoded"] is False

    for aquarium in doc["aquaria"]:
        assert aquarium["intent"]["planning_may_read_goal"] is True
        assert aquarium["intent"]["physics_may_read_goal"] is False
        assert aquarium["integrity"]["planning_metadata_changes_physics"] is False
        assert aquarium["integrity"]["scientific_promotion_effect"] is False


def test_current_aquaria_do_not_seed_target_outcomes():
    doc = load_json("aquaria/registry.json")
    for aquarium in doc["aquaria"]:
        integrity = aquarium["integrity"]
        assert integrity["target_outcome_seeded"] is False
        assert integrity["target_morphology_seeded"] is False
        assert integrity["outcome_location_seeded"] is False
        assert integrity["outcome_time_seeded"] is False
