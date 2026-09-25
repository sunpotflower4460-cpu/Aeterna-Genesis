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


@pytest.mark.parametrize("wid", sorted(whites.registry()))
@pytest.mark.parametrize("corner", ["lo", "hi", "hi-instant-quench"])
def test_every_allowed_law_setting_stays_numerically_finite(wid, corner):
    """Knob ranges are bounded by the integrators' stability, so a person cannot drive a white into NaNs
    (a numerical blow-up would look like 'physics' in the tank)."""
    import numpy as np
    from tools.lab.universe import Universe
    w = whites.get(wid)
    law = {k.name: (k.lo if corner == "lo" else k.hi) for k in w.knobs if k.kind == "law"}
    if corner == "hi-instant-quench":
        if wid != "tdgl-3d":
            pytest.skip("TDGL only")
        law["quench_duration"] = 0.0          # eps = +eps_final from t=0 (the other extreme starts at -eps_final)
    u = Universe(wid, 0, law)
    u.advance(3 * w.steps_per_frame if w.dimension == 3 else 20 * w.steps_per_frame)
    assert u.finite(), f"{wid} diverged at {law}"
    assert all(np.isfinite(v) for v in u.metrics().values() if isinstance(v, float) and v == v)
