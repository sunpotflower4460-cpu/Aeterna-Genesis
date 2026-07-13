"""g002 -> C3 child Room: the temperature GRADIENT is GENERATED from an absorbed energy flux, not imposed
as a fixed ΔT (docs/CAUSAL_CLOSURE.md). no_touch: the official parent room-g002-a is NOT modified.
"""

import json
import pathlib

import jsonschema
import yaml

from genesis.models import boussinesq_flux_heated as fh

ROOT = pathlib.Path(__file__).resolve().parents[1]
CAND = ROOT / "rooms" / "candidates" / "room-g002-c3-flux"


def test_gradient_is_generated_and_convection_emerges_from_rest():
    """From a UNIFORM temperature + noise (NO gradient placed), the absorbed flux GENERATES a vertical
    gradient (grows far above the t=0 noise) and convection EMERGES from rest (KE 0 -> >0, Nu > 1)."""
    r = fh.run_flux_heated(seed=0)
    assert r["converged"] and r["finite"]
    assert r["ke_start"] == 0.0                                   # starts at rest (no seeded flow)
    assert r["gradient_start"] < 0.2                              # t=0 temperature is uniform (noise only)
    assert r["gradient_final"] > 20.0 * r["gradient_start"]       # the flux GENERATED the gradient
    assert r["gradient_generated"] is True
    assert r["ke_final"] > 1.0 and r["nusselt"] > 1.02            # convection emerged from the developed gradient
    assert r["convection_from_rest"] is True
    # deterministic
    r2 = fh.run_flux_heated(seed=0)
    assert abs(r2["gradient_final"] - r["gradient_final"]) < 1e-6


def test_c3_room_is_candidate_not_official_and_no_gradient_seeded():
    """The child Room is a CANDIDATE (official:false; parent not overwritten), starts quiescent (no gradient
    placed), and records causal_closure_level C3."""
    room = yaml.safe_load((CAND / "room.yaml").read_text())
    assert room["official"] is False and room["parent_room"] == "room-g002-a"
    genesis = yaml.safe_load((CAND / "genesis.yaml").read_text())
    assert genesis["initial_state"]["type"] == "quiescent_plus_noise"   # no ΔT / gradient imposed
    assert genesis["protocol"]["drive"]["type"] == "absorbed_flux_heating"
    emg = json.loads((CAND / "emergence.json").read_text())
    assert emg["measured_by"]["gradient_seeded"] is False and emg["measured_by"]["gradient_generated"] is True
    anc = yaml.safe_load((CAND / "causal-ancestry.yaml").read_text())
    assert anc["causal_closure_level"] == "C3"                # causal-closure level lives in causal-ancestry.yaml


def test_c3_room_yamls_validate_against_schemas():
    """The child Room's genesis/room/provenance/causal-ancestry validate against the repo schemas; the
    gradient is an emerged_state (manually_set:false) and the flux carries claim_excludes."""
    def _schema(name):
        return json.loads((ROOT / "schemas" / name).read_text())
    jsonschema.validate(yaml.safe_load((CAND / "genesis.yaml").read_text()), _schema("genesis.schema.json"))
    jsonschema.validate(yaml.safe_load((CAND / "room.yaml").read_text()), _schema("room.schema.json"))
    prov = yaml.safe_load((CAND / "provenance.yaml").read_text())
    jsonschema.validate(prov, _schema("provenance.schema.json"))
    jsonschema.validate(yaml.safe_load((CAND / "causal-ancestry.yaml").read_text()),
                        _schema("causal-ancestry.schema.json"))
    by_name = {e["name"]: e for e in prov["entries"]}
    assert by_name["temperature_gradient"]["input_class"] == "emerged_state"
    assert by_name["temperature_gradient"]["manually_set"] is False       # gradient generated, not placed
    assert "spontaneous_energy_flux" in by_name["absorbed_energy_flux"]["claim_excludes"]


def test_official_g002_room_untouched():
    """no_touch: the official parent still imposes a fixed temperature difference (unchanged)."""
    g = yaml.safe_load((ROOT / "rooms" / "official" / "room-g002-a" / "genesis.yaml").read_text())
    assert g["protocol"]["drive"]["type"] == "fixed_temperature_difference"
    assert g["initial_state"]["type"] == "quiescent_plus_noise"
