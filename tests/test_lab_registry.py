"""Live lab registry: the knobs a person can touch are the models' own parameters, with sane ranges."""
import json

import pytest

from tools.lab import whites


@pytest.mark.parametrize("wid", sorted(whites.registry()))
def test_knob_defaults_match_model_defaults(wid):
    w = whites.get(wid)
    for k in w.knobs:
        assert k.kind in ("law", "start")
        assert k.lo <= k.default <= k.hi, k
        if k.name in w.defaults:
            assert w.defaults[k.name] == pytest.approx(k.default), f"{wid}.{k.name} differs from the model DEFAULTS"
        elif k.kind == "law":
            pytest.fail(f"{wid}.{k.name}: a law knob must be a parameter the model reads")


@pytest.mark.parametrize("wid", sorted(whites.registry()))
def test_public_spec_is_json_and_complete(wid):
    spec = whites.get(wid).public()
    json.dumps(spec)
    assert spec["lenses"] and spec["put_in"] and spec["perturbs"]
    assert spec["dimension"] in (2, 3)


def test_start_knobs_cannot_change_mid_run():
    w = whites.get("gray-scott")
    with pytest.raises(ValueError):
        w.check_knobs({"n_seeds": 3}, allow_start=False)
    with pytest.raises(ValueError):
        w.check_knobs({"F": 0.5})
    with pytest.raises(KeyError):
        w.check_knobs({"not_a_knob": 1})
