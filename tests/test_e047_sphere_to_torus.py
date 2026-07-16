"""e047 sphere-to-torus (P06 / F1) tests -- V0 topology check + V1 fixed-shape free-energy crossing (role V).

All fast/synthetic. They assert: (V0) the Topology Instrument reads the diffuse-interface ball/torus volume
Betti numbers, (V1) the nematic free energy has the right bulk minimiser, descends monotonically, and
reproduces the sphere->torus crossing which VANISHES when planar anchoring is turned off (mechanism control).
"""
import numpy as np

from genesis.diagnostics import topology_betti as tb
from genesis.models import nematic_qtensor as nq

P = nq.FROZEN


# ---------------- V0 ----------------
def test_v0_diffuse_ball_is_simply_connected():
    b = tb.betti3d(nq.phi_ball(28, 7.0, P["eps"]) > 0.0)
    assert (b["b0"], b["b1"], b["b2"], b["genus"]) == (1, 0, 0, 0)


def test_v0_diffuse_torus_has_one_volume_handle():
    R, a = nq.torus_from_ball(7.0)
    b = tb.betti3d(nq.phi_torus(28, R, a, P["eps"]) > 0.0)
    assert b["b0"] == 1 and b["b1"] == 1 and b["b2"] == 0 and b["genus"] == 1


def test_v0_threshold_and_resolution_robustness():
    R, a = nq.torus_from_ball(8.0)
    pt = nq.phi_torus(32, R, a, P["eps"])
    for phic in (-0.3, -0.1, 0.0, 0.1, 0.3):
        assert tb.betti3d(pt > phic)["b1"] == 1           # phi_c robust
    R2, a2 = nq.torus_from_ball(8.0 * 24 / 32)
    assert tb.betti3d(nq.phi_torus(24, R2, a2, P["eps"]) > 0.0)["b1"] == 1   # coarser N still b1=1


# ---------------- V1 physics ----------------
def test_bulk_minimiser_matches_analytic_S_eq():
    Seq = nq.s_eq(P["A_in"], P["B"], P["C"])
    phi = np.ones((14, 14, 14))                            # all interior, no interface
    q, _h, _t = nq.relax(phi, W=0.0, p=P, steps=250, seed=1, kind="uniform")
    c = 7
    Qm = np.array([[q[0][c, c, c], q[1][c, c, c], q[2][c, c, c]],
                   [q[1][c, c, c], q[3][c, c, c], q[4][c, c, c]],
                   [q[2][c, c, c], q[4][c, c, c], -(q[0][c, c, c] + q[3][c, c, c])]])
    S_meas = 1.5 * np.sort(np.linalg.eigvalsh(Qm))[-1]
    assert abs(S_meas - Seq) < 0.02


def test_frank_gradient_flow_is_monotone():
    phi = nq.phi_ball(24, 6.0, P["eps"])
    _n1, t1 = nq.frank_relax(phi, W=2.0, K=0.3, p=P, steps=1, kind="random")
    _n2, t2 = nq.frank_relax(phi, W=2.0, K=0.3, p=P, steps=200, kind="random")
    assert t2["total"] < t1["total"]


def test_planar_anchoring_penalises_normal_more_than_tangential():
    phi = nq.phi_ball(24, 6.0, P["eps"])
    vx, vy, vz, _g = nq.interface_normal(phi)
    N = phi.shape[0]
    # homeotropic (n = surface normal) vs a uniform (mostly tangential) director
    homeo = (vx, vy, vz)
    z = np.zeros((N, N, N))
    unif = (z, z, np.ones((N, N, N)))
    e_homeo = nq.frank_energy(homeo, phi, W=1.0, K=0.0, p=P)["anchoring"]
    e_unif = nq.frank_energy(unif, phi, W=1.0, K=0.0, p=P)["anchoring"]
    assert e_homeo > e_unif > 0.0


# ---------------- V1 crossing + control ----------------
def test_sphere_torus_crossing_exists_and_control_removes_it():
    Ks = [0.02, 0.16, 0.35, 0.60]
    on = nq.sphere_torus_crossing_frank(24, 6.0, Ks, W=2.0, p=P, steps=200, seeds=(0,))
    assert on["K_star"] is not None
    assert on["rows"][0]["dF"] > 0.0 and on["rows"][-1]["dF"] < 0.0     # ball -> torus as K grows
    off = nq.sphere_torus_crossing_frank(24, 6.0, Ks, W=0.0, p=P, steps=200, seeds=(0,))
    assert off["K_star"] is None and all(r["dF"] > 0.0 for r in off["rows"])   # anchoring off -> no crossing


def test_qtensor_full_functional_does_not_cross_here():
    """Companion fact (F2-relevant): with 3D escape allowed the torus stays higher (no fixed-shape crossing)."""
    p = P
    R, a = nq.torus_from_ball(5.0)
    qb = nq.phi_ball(20, 5.0, p["eps"])
    qt = nq.phi_torus(20, R, a, p["eps"])
    _q1, _h1, tb_ = nq.relax(qb, 2.0, p, 140, seed=0, kind="azimuthal")
    _q2, _h2, tt_ = nq.relax(qt, 2.0, p, 140, seed=0, kind="azimuthal")
    assert tt_["total"] > tb_["total"]
