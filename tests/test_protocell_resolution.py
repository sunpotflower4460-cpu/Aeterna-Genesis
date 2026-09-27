"""P17: the resolution verdict compares every grid spacing, and refuses to judge a single one."""
import json

from tools import protocell_resolution as pres


def _write(tmp_path, dx, seed, density):
    obs = {k: 1.0 for k in pres.OBS}
    obs.update(density=density, containers=10, n_inherit=5, late_frames=4)
    rec = {"dim": 3, "L": 32.0, "dx": dx, "n": int(32 / dx), "seed": seed, "T": 200.0, "obs": obs}
    (tmp_path / f"res3d_dx{dx:.4f}_s{seed}.json").write_text(json.dumps(rec))


def test_a_single_spacing_gives_no_verdict(tmp_path):
    for s in (1, 2):
        _write(tmp_path, 1.0, s, 1.0)
    t = pres.summary(tmp_path)[3]
    assert t["insufficient"] and t["verdict"] == {}


def test_a_divergent_middle_spacing_is_caught(tmp_path):
    for dx, d in ((1.0, 1.0), (0.8, 2.0), (0.6666666667, 1.0)):     # the ends agree, the middle does not
        for s in (1, 2):
            _write(tmp_path, dx, s, d)
    v = pres.summary(tmp_path)[3]["verdict"]["density"]
    assert not v["resolution_independent"] and 0.8 in v["widest_pair"]
    assert pres.summary(tmp_path)[3]["verdict"]["box_share"]["resolution_independent"]
