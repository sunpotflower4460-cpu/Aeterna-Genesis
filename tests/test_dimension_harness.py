"""PR5 test: the Dimension Transfer Harness measures out-of-plane risk and emits a schema-valid report."""

import json
import os

from jsonschema import Draft202012Validator

from genesis.dimension import harness

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_report_validates_against_schema():
    doc, st = harness.report(quick=True)
    schema = json.load(open(os.path.join(_REPO, "schemas", "dimension-transfer.schema.json")))
    Draft202012Validator(schema).validate(doc)
    assert doc["dimension_risk"]["topology_codimension_change"] == "high"  # 2D vortex -> 3D vortex line
    assert doc["status"] == "audit_passed"


def test_slab_measures_out_of_plane_and_keeps_lines():
    st = harness.slab_test(quick=True)
    # residual vortices must exist to make the test non-degenerate (edge>=48 keeps them)
    assert st["defects_2d_initial"] > 0
    # measured out-of-plane growth is a real number; at this scale the vortex lines stay coherent
    assert isinstance(st["out_of_plane_growth"], float)
    assert st["structure_maintained"] is True
    assert st["escaped_out_of_plane"] is False


def test_harness_is_a_risk_report_not_a_gate():
    doc, _ = harness.report(quick=True)
    # a linear proxy for out-of-plane mode growth is recorded (number), full-3D still required
    assert "out_of_plane_growth_rate" in doc["linear_analysis"]
