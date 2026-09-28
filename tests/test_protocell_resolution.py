"""P17: the resolution verdict compares every grid spacing, and refuses to judge a single one."""
import json

from tools import protocell_resolution as pres


def _write(tmp_path, dx, seed, density):
    obs = {k: 1.0 for k in pres.OBS}
    obs.update(density=density, containers=10, n_inherit=5, late_frames=4)
    rec = {"dim": 3, "L": 32.0, "dx": dx, "n": int(32 / dx), "seed": seed, "T": 200.0, "obs": obs}
    (tmp_path / f"res3d_L32_T200_dx{dx:.4f}_s{seed}.json").write_text(json.dumps(rec))


def _only(table):
    assert len(table) == 1
    return next(iter(table.values()))


def test_a_single_spacing_gives_no_verdict(tmp_path):
    for s in (1, 2):
        _write(tmp_path, 1.0, s, 1.0)
    t = _only(pres.summary(tmp_path))
    assert t["insufficient"] and t["verdict"] == {}


def test_a_divergent_middle_spacing_is_caught(tmp_path):
    for dx, d in ((1.0, 1.0), (0.8, 2.0), (0.6666666667, 1.0)):     # the ends agree, the middle does not
        for s in (1, 2):
            _write(tmp_path, dx, s, d)
    v = _only(pres.summary(tmp_path))["verdict"]["density"]
    assert not v["resolution_independent"] and 0.8 in v["widest_pair"]
    assert _only(pres.summary(tmp_path))["verdict"]["box_share"]["resolution_independent"]


def test_a_spacing_that_does_not_tile_the_box_is_rejected(tmp_path):
    import pytest
    with pytest.raises(SystemExit):
        pres.main(["run", "--dim", "2", "--L", "32", "--dx", "0.7", "--T", "1", "--out", str(tmp_path)])
    assert not list(tmp_path.glob("res*.json"))


def test_refining_keeps_the_noise_strength_per_physical_volume():
    import numpy as np
    from genesis.models import protocell_one as po
    from tools import protocell_run as pr
    r = pr.run(2, seed=1, T=0.0, n=64, model=po, dx=0.5, overrides={"n_seeds": 0})
    q = r["params"]
    assert np.isclose(q["dt"], po.DEFAULTS_2D["dt"] * 0.5 ** 4) and np.isclose(q["seed_radius"], 6.0)
    assert np.isclose(q["noise"], po.DEFAULTS_2D["noise"] / 0.5)             # per-cell std ∝ dx^(−dim/2), dim = 2


def test_runs_of_another_box_or_duration_are_not_mixed(tmp_path):
    _write(tmp_path, 1.0, 1, 1.0)
    rec = json.loads((tmp_path / "res3d_L32_T200_dx1.0000_s1.json").read_text())
    rec.update(dx=0.8, L=40.0)
    (tmp_path / "res3d_L40_T200_dx0.8000_s1.json").write_text(json.dumps(rec))
    t = pres.summary(tmp_path)
    assert len(t) == 2 and all(v["insufficient"] for v in t.values())


def test_an_observable_missing_at_one_spacing_gets_no_verdict(tmp_path):
    for dx in (1.0, 0.8):
        _write(tmp_path, dx, 1, 1.0)
    f = tmp_path / "res3d_L32_T200_dx0.8000_s1.json"
    rec = json.loads(f.read_text())
    rec["obs"]["inheritance"] = None
    f.write_text(json.dumps(rec))
    v = _only(pres.summary(tmp_path))["verdict"]["inheritance"]
    assert v["insufficient"] and v["resolution_independent"] is None and v["missing_dx"] == [0.8]


def test_a_seed_without_a_value_gets_no_verdict(tmp_path):
    for dx in (1.0, 0.8):
        for s in (1, 2):
            _write(tmp_path, dx, s, 1.0)
    f = tmp_path / "res3d_L32_T200_dx1.0000_s2.json"
    rec = json.loads(f.read_text())
    rec["obs"]["inheritance"] = None                                  # seed 2 had no scorable division
    f.write_text(json.dumps(rec))
    v = _only(pres.summary(tmp_path))["verdict"]["inheritance"]
    assert v["insufficient"] and v["incomplete_seeds_dx"] == [1.0]


def test_different_seed_sets_are_not_compared(tmp_path):
    for s in (1, 2):
        _write(tmp_path, 1.0, s, 1.0)
    for s in (3, 4):
        _write(tmp_path, 0.8, s, 1.0)
    t = _only(pres.summary(tmp_path))
    assert t["insufficient"] and "different seeds" in t["reason"]


def test_runs_with_a_different_law_are_not_compared(tmp_path):
    for dx in (1.0, 0.8):
        for s in (1, 2):
            _write(tmp_path, dx, s, 1.0)
    for f in tmp_path.glob("res3d_*.json"):
        rec = json.loads(f.read_text())
        dx = rec["dx"]
        rec["params"] = {"dx": dx, "dt": 0.01 * dx ** 4, "seed_radius": 3.0 / dx, "noise": 0.02 * dx ** -1.5,
                         "hyd": 0.1 if dx == 1.0 else 0.2}                    # the law differs at dx = 0.8
        f.write_text(json.dumps(rec))
    t = _only(pres.summary(tmp_path))
    assert t["insufficient"] and "different laws" in t["reason"]
    for f in tmp_path.glob("res3d_*.json"):                                 # same law, only dx-scaled entries differ
        rec = json.loads(f.read_text())
        rec["params"]["hyd"] = 0.1
        f.write_text(json.dumps(rec))
    assert not _only(pres.summary(tmp_path))["insufficient"]
