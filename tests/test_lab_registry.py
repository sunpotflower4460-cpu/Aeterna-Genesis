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


def _corners(w):
    """Every corner of the law-knob box for whites with <= 2 law knobs (the others: all-lo and all-hi)."""
    import itertools
    law = [k for k in w.knobs if k.kind == "law"]
    if len(law) <= 2:
        return [dict(zip([k.name for k in law], c)) for c in itertools.product(*[(k.lo, k.hi) for k in law])]
    return [{k.name: k.lo for k in law}, {k.name: k.hi for k in law}]


def _check_finite(wid, frames_2d, seeds):
    import numpy as np
    from tools.lab.universe import Universe
    w = whites.get(wid)
    cases = _corners(w)
    if wid == "tdgl-3d":
        cases.append({**cases[-1], "quench_duration": 0.0})   # eps = +eps_final from t=0
    frames = 3 if w.dimension == 3 else frames_2d
    for law in cases:
        for seed in seeds if w.dimension == 2 else (0,):
            u = Universe(wid, seed, law)
            u.advance(frames * w.steps_per_frame)
            assert u.finite(), f"{wid} diverged at {law} seed {seed}"
            assert all(np.isfinite(v) for v in u.metrics().values() if isinstance(v, float) and v == v)


@pytest.mark.parametrize("wid", sorted(whites.registry()))
def test_every_allowed_law_setting_stays_numerically_finite(wid):
    """Knob ranges are bounded by the integrators' stability, so a person cannot drive a white into NaNs
    (a numerical blow-up would look like 'physics' in the tank)."""
    _check_finite(wid, frames_2d=25, seeds=(0,))


@pytest.mark.parametrize("wid", sorted(w for w in whites.registry() if whites.get(w).dimension == 2))
def test_law_corners_stay_finite_longer(wid):
    """The same corners, three seeds and 80 frames (listed in tests/slow_tests.txt; weekly-integrity)."""
    _check_finite(wid, frames_2d=80, seeds=(0, 1, 2))
