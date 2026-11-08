"""Scenarios T1–T10 of the P10 transport audit (v0.1).

Every number used here is read from PRE_REGISTRATION.json. Each check appends one row to `rows`
with its own PASS / FAIL / INCONCLUSIVE verdict. A test's verdict is the worst of its rows.
Nothing in this file clips, floors or edits a concentration.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, REPO)

import model  # noqa: E402
import solver  # noqa: E402
import metrics as M  # noqa: E402

with open(os.path.join(HERE, "PRE_REGISTRATION.json"), encoding="utf-8") as fh:
    P = json.load(fh)
TOL = P["tolerances"]
GEO = P["geometry"]
PAR = P["parameters"]
TIME = P["time"]
INT = P["integrators"]
X0 = 0.5
L = 1.0
M0 = 1.0
RANK = {"PASS": 0, "INCONCLUSIVE": 1, "FAIL": 2}


def ic(x):
    """Pre-registered initial condition c0 = 1 + 0.5 cos(2 pi x / L)."""
    return 1.0 + 0.5 * np.cos(2.0 * np.pi * x / L)


def check(rows, tid, case, N, integ, metric, value, thr, op):
    """Append one row. op: '<=' or '>=' (PASS if condition holds, else FAIL)."""
    ok = (value <= thr) if op == "<=" else (value >= thr)
    rows.append({"test_id": tid, "case": case, "N": N, "integrator": integ, "metric": metric,
                 "value": float(value), "threshold": float(thr), "op": op,
                 "verdict": "PASS" if ok else "FAIL"})


def order_row(rows, tid, case, metric, p, pass_thr, inc_thr, N="", integ=""):
    """Convergence-order verdict: PASS if p >= pass_thr; INCONCLUSIVE if inc_thr <= p < pass_thr; else FAIL."""
    if not np.isfinite(p):
        v = "INCONCLUSIVE"
    elif p >= pass_thr:
        v = "PASS"
    elif p >= inc_thr:
        v = "INCONCLUSIVE"
    else:
        v = "FAIL"
    rows.append({"test_id": tid, "case": case, "N": N, "integrator": integ, "metric": metric,
                 "value": float(p), "threshold": float(pass_thr), "op": ">= (order)",
                 "verdict": v})


def test_verdict(rows, tid):
    vs = [r["verdict"] for r in rows if r["test_id"] == tid]
    if not vs:
        return "NOT_RUN"
    return max(vs, key=lambda v: RANK[v])


def _eq_run(N, beta, D_kind="const", D0=1.0, width=0.05, c0=None, t_eval=None, kind="mu"):
    """Run one species from the pre-registered IC to t_eval with BDF. Returns (x, phi, dx, run)."""
    dx, x = model.grid(N, L)
    phi = model.phi_profile(x, X0, width)
    D = model.D_field(phi, D0, D_kind)
    s = solver.make_setup(N, phi, D, beta, dx, kind)
    if c0 is None:
        c0 = ic(x)
    if t_eval is None:
        t_eval = [0.0, TIME["t_eq"]]
    run = solver.run_bdf(s, c0, t_eval, rtol=INT["rtol_primary"], atol=INT["atol_primary"])
    return {"x": x, "phi": phi, "dx": dx, "D": D, "setup": s, "run": run, "beta": beta, "N": N,
            "width": width}


# ---------------------------------------------------------------- T1
def T1():
    rows = []
    N = 32
    dx, x = model.grid(N, L)
    rng = np.random.default_rng(1)
    phi = np.clip(0.8 * np.sin(3 * np.pi * x) + 0.1 * rng.standard_normal(N), -0.95, 0.95)
    m = 0.3 + 0.2 * np.sin(2 * np.pi * x)
    c1 = 0.5 + rng.random(N)
    c2 = 0.5 + rng.random(N)
    betas = [0.5, -0.5]
    a, k0, al = 1.0, 1.0, 0.5
    eps = 1e-6

    def F(c1_, c2_, phi_, m_):
        return model.free_energy_phi_full([c1_, c2_], phi_, m_, betas, dx, a=a, kappa0=k0, alpha=al)

    def fd(fun, arr, j):
        ap = arr.copy(); ap[j] += eps
        am = arr.copy(); am[j] -= eps
        return (fun(ap) - fun(am)) / (2 * eps)

    # species variation: dF/dc_{i,j} = dx * mu_{i,j}
    exp_c = model.mu_species(c1, phi, betas[0]) * dx
    fd_c = np.array([fd(lambda v: F(v, c2, phi, m), c1, j) for j in range(N)])
    err_c = np.max(np.abs(fd_c - exp_c)) / max(np.max(np.abs(exp_c)), 1e-12)
    check(rows, "T1", "species_A_dF/dc", N, "FD", "relative_error_max", err_c, TOL["T1_fd_relative_error_max"], "<=")

    # phi variation: dF/dphi_j = dx * mu_phi_j (includes -div(kappa grad phi), chi sum)
    exp_p = model.mu_phi_discrete([c1, c2], phi, m, betas, dx, a=a, kappa0=k0, alpha=al) * dx
    fd_p = np.array([fd(lambda v: F(c1, c2, v, m), phi, j) for j in range(N)])
    err_p = np.max(np.abs(fd_p - exp_p)) / max(np.max(np.abs(exp_p)), 1e-12)
    check(rows, "T1", "phi_dF/dphi", N, "FD", "relative_error_max", err_p, TOL["T1_fd_relative_error_max"], "<=")

    # m variation: dF/dm_j = dx * (kappa'(m)/4)(Dphi_+^2 + Dphi_-^2)/dx^2
    exp_m = model.mu_m_interface_discrete(m, phi, dx, kappa0=k0, alpha=al) * dx
    fd_m = np.array([fd(lambda v: F(c1, c2, phi, v), m, j) for j in range(N)])
    err_m = np.max(np.abs(fd_m - exp_m)) / max(np.max(np.abs(exp_m)), 1e-12)
    check(rows, "T1", "m_dF/dm_interface", N, "FD", "relative_error_max", err_m, TOL["T1_fd_relative_error_max"], "<=")

    # sensitivity: the div form must differ from the naive kappa*lap form when kappa varies
    div_form = model.mu_phi_discrete([], phi, m, [], dx, a=0.0, kappa0=k0, alpha=al)
    naive = model.naive_laplacian_term(m, phi, dx, kappa0=k0, alpha=al)
    sens = np.max(np.abs(div_form - naive)) / np.max(np.abs(div_form))
    check(rows, "T1", "sensitivity_div_vs_naive_lap", N, "analytic", "relative_difference_max", sens,
          TOL["T1_sensitivity_min_divform_vs_naive_laplacian_relative"], ">=")
    return rows


# ---------------------------------------------------------------- T7 helper: boundary structure
def boundary_structure_check(rows):
    rng = np.random.default_rng(7)
    for N in (32, 128):
        dx, x = model.grid(N, L)
        phi = model.phi_profile(x)
        D = model.D_field(phi, 1.0, "linear")
        c = 0.5 + rng.random(N)
        for name, J in (("mu", model.flux_mu(c, phi, 0.5, D, dx)),
                        ("fick", model.flux_fick(c, D, dx))):
            rhs = model.rhs_from_flux(J, dx)
            total = np.sum(rhs) * dx
            scale = max(1.0, np.sum(np.abs(rhs)) * dx)
            check(rows, "T7", f"boundary_sum_rhs_{name}", N, "structural", "|sum rhs dx| / scale",
                  abs(total) / scale, TOL["T7_boundary_rhs_sum_rel_max"], "<=")
            check(rows, "T7", f"wall_flux_zero_{name}", N, "structural", "|J_0|+|J_N|",
                  abs(J[0]) + abs(J[-1]), 0.0, "<=")


# ---------------------------------------------------------------- T2
def T2():
    rows = []
    N = GEO["N_main"]
    beta = PAR["beta_chi_over_RT"]["A_positive"]
    tv = [0.0, TIME["t_check"], TIME["t_eq"]]
    A = _eq_run(N, beta, D_kind="linear", t_eval=tv, kind="fick")
    B = _eq_run(N, beta, D_kind="linear", t_eval=tv, kind="mu")
    for name, R in (("A_fick", A), ("B_mu", B)):
        if R["run"]["C"].shape[0] != 3:
            check(rows, "T2", name + "_integrator_success", N, "BDF", "n_saved", R["run"]["C"].shape[0], 3, ">=")
    rA = M.partition_ratio_measured(A["run"]["C"][-1], A["x"])
    rB = M.partition_ratio_measured(B["run"]["C"][-1], B["x"])
    pB = M.partition_ratio_predicted_discrete(B["phi"], beta, B["x"])
    check(rows, "T2", "A_fick_ratio_minus_one", N, "BDF", "|ratio-1|", abs(rA - 1.0),
          TOL["T2_fick_partition_ratio_abs_minus_one_max"], "<=")
    check(rows, "T2", "B_mu_partition_rel_error", N, "BDF", "relative error vs discrete law",
          abs(rB - pB) / pB, TOL["T2_B_partition_discrete_rel_max"], "<=")
    return rows, {"A_ratio": rA, "B_ratio": rB, "B_pred": pB, "A_final": A["run"]["C"][-1],
                  "B_final": B["run"]["C"][-1], "A_run": A, "B_run": B}


# ---------------------------------------------------------------- T3 (+ sharp stress)
def T3():
    rows = []
    out = {}
    cont_err = {}
    for N in GEO["N_list_convergence"]:
        R = _eq_run(N, PAR["beta_chi_over_RT"]["A_positive"], t_eval=[0.0, TIME["t_eq"]])
        run, x, phi, dx, beta = R["run"], R["x"], R["phi"], R["dx"], R["beta"]
        C = run["C"]
        check(rows, "T3", "solver_success", N, "BDF", "success(1=yes)", float(run["success"]), 1.0, ">=")
        check(rows, "T3", "mass_residual", N, "BDF", "max |M-M0|/M0", M.mass_residual_rel(C, dx, M0),
              TOL["T3_mass_residual_rel_max"], "<=")
        ceq = M.discrete_equilibrium(phi, beta, M0, dx)
        cf = C[-1]
        check(rows, "T3", "boltzmann_cv_at_t_eq", N, "BDF", "CV(c exp(beta phi))",
              M.boltzmann_invariant_cv(cf, phi, beta), TOL["T3_boltzmann_cv_at_t_eq_max"], "<=")
        check(rows, "T3", "discrete_eq_rel_dev", N, "BDF", "max rel dev from c_disc",
              float(np.max(np.abs(cf - ceq) / ceq)), TOL["T3_discrete_equilibrium_rel_max"], "<=")
        check(rows, "T3", "mu_spread_at_t_eq", N, "BDF", "max |mu - mean mu|",
              M.mu_spread(cf, phi, beta), TOL["T3_mu_spread_at_t_eq_max"], "<=")
        check(rows, "T3", "max_face_flux_at_t_eq", N, "BDF", "max |J|",
              M.max_face_flux(cf, phi, beta, R["D"], dx), TOL["T3_max_face_flux_at_t_eq_max"], "<=")
        r_meas = M.partition_ratio_measured(cf, x)
        r_disc = M.partition_ratio_predicted_discrete(phi, beta, x)
        r_cont = M.partition_ratio_predicted_continuum(beta, lambda z: model.phi_profile(z))
        check(rows, "T3", "partition_rel_error_vs_discrete", N, "BDF", "rel error",
              abs(r_meas - r_disc) / r_disc, TOL["T3_partition_discrete_rel_max"], "<=")
        cont_err[N] = abs(r_meas - r_cont) / r_cont
        out[N] = {"ratio_meas": r_meas, "ratio_disc": r_disc, "ratio_cont": r_cont, "C_final": cf,
                  "run": run, "x": x, "phi": phi, "dx": dx}
    check(rows, "T3", "partition_continuum_rel_error_N128", 128, "BDF", "rel error vs continuum",
          cont_err[128], TOL["T3_partition_continuum_rel_max_at_N128"], "<=")
    p1 = M.observed_order(cont_err[64], cont_err[128])
    p2 = M.observed_order(cont_err[128], cont_err[256])
    order_row(rows, "T3", "continuum_error_order_64_128", "observed order", p1, 1.5, 0.5, 128, "BDF")
    order_row(rows, "T3", "continuum_error_order_128_256", "observed order", p2, 1.5, 0.5, 256, "BDF")
    # sharp stress case
    Rs = _eq_run(256, 1.5, width=0.02, t_eval=[0.0, TIME["t_eq"]])
    cfs = Rs["run"]["C"][-1]
    check(rows, "T3", "sharp_boltzmann_cv_at_t_eq", 256, "BDF", "CV", M.boltzmann_invariant_cv(cfs, Rs["phi"], 1.5),
          TOL["T3_sharp_boltzmann_cv_max"], "<=")
    check(rows, "T3", "sharp_min_c_positive", 256, "BDF", "min c", float(cfs.min()), 0.0, ">=")
    rs_meas = M.partition_ratio_measured(cfs, Rs["x"])
    rs_disc = M.partition_ratio_predicted_discrete(Rs["phi"], 1.5, Rs["x"])
    check(rows, "T3", "sharp_partition_rel_error", 256, "BDF", "rel error",
          abs(rs_meas - rs_disc) / rs_disc, TOL["T3_partition_discrete_rel_max"], "<=")
    out["sharp"] = {"C_final": cfs, "x": Rs["x"], "phi": Rs["phi"], "ratio_meas": rs_meas,
                    "ratio_disc": rs_disc}
    out["cont_err"] = cont_err
    return rows, out


# ---------------------------------------------------------------- T4
def T4():
    rows = []
    N = GEO["N_main"]
    bA = PAR["beta_chi_over_RT"]["A_positive"]
    bB = PAR["beta_chi_over_RT"]["B_negative"]
    RA = _eq_run(N, bA)
    RB = _eq_run(N, bB)
    rA = M.partition_ratio_measured(RA["run"]["C"][-1], RA["x"])
    rB = M.partition_ratio_measured(RB["run"]["C"][-1], RB["x"])
    pA = M.partition_ratio_predicted_discrete(RA["phi"], bA, RA["x"])
    pB = M.partition_ratio_predicted_discrete(RB["phi"], bB, RB["x"])
    check(rows, "T4", "A_partition_rel_error", N, "BDF", "rel error", abs(rA - pA) / pA,
          TOL["T4_partition_discrete_rel_max"], "<=")
    check(rows, "T4", "B_partition_rel_error", N, "BDF", "rel error", abs(rB - pB) / pB,
          TOL["T4_partition_discrete_rel_max"], "<=")
    S = rB / rA
    check(rows, "T4", "selectivity_S_B_over_A", N, "BDF", "S = ratio_B / ratio_A", S,
          TOL["T4_selectivity_S_min"], ">=")
    return rows, {"rA": rA, "rB": rB, "pA": pA, "pB": pB, "S": S, "RA": RA, "RB": RB}


# ---------------------------------------------------------------- T5
def T5():
    rows = []
    N = GEO["N_main"]
    b = PAR["beta_chi_over_RT"]["equal_control"]
    R1 = _eq_run(N, b)
    R2 = _eq_run(N, b)  # second species, identical chi, identical D, identical IC
    r1 = M.partition_ratio_measured(R1["run"]["C"][-1], R1["x"])
    r2 = M.partition_ratio_measured(R2["run"]["C"][-1], R2["x"])
    check(rows, "T5", "equal_chi_ratio_abs_diff", N, "BDF", "|r_A - r_B|", abs(r1 - r2),
          TOL["T5_equal_chi_ratio_abs_diff_max"], "<=")
    R0 = _eq_run(N, PAR["beta_chi_over_RT"]["zero_control"])
    check(rows, "T5", "zero_chi_max_abs_c_minus_1", N, "BDF", "max |c - 1| at t_eq",
          float(np.max(np.abs(R0["run"]["C"][-1] - 1.0))), TOL["T5_zero_chi_max_abs_c_minus_1"], "<=")
    return rows, {"R0": R0}


# ---------------------------------------------------------------- T6
def T6():
    rows = []
    N = GEO["N_main"]
    b = PAR["beta_chi_over_RT"]["A_positive"]
    t_fine = np.arange(0.0, TIME["t_eq"] + 1e-12, 1e-3)
    results = {}
    cases = [("const_D0.25", "const", 0.25), ("const_D1", "const", 1.0), ("const_D4", "const", 4.0),
             ("linear_D1", "linear", 1.0)]
    dx, x = model.grid(N, L)
    phi = model.phi_profile(x)
    ceq = M.discrete_equilibrium(phi, b, M0, dx)
    for name, kind, D0 in cases:
        R = _eq_run(N, b, D_kind=kind, D0=D0, t_eval=t_fine)
        C = R["run"]["C"]
        r_end = M.partition_ratio_measured(C[-1], x)
        r_pred = M.partition_ratio_predicted_discrete(phi, b, x)
        check(rows, "T6", f"{name}_partition_across_D", N, "BDF", "|r_end - r_pred| / r_pred",
              abs(r_end - r_pred) / r_pred, TOL["T6_partition_across_D_rel_max"], "<=")
        trel = M.relaxation_time(t_fine, C, ceq, 1e-2)
        results[name] = {"t_rel": trel, "D0": D0, "kind": kind}
    t1 = results["const_D1"]["t_rel"]
    for name in ("const_D0.25", "const_D4"):
        Dv = results[name]["D0"]
        scale_err = abs(results[name]["t_rel"] * Dv - t1 * 1.0) / (t1 * 1.0)
        check(rows, "T6", f"{name}_time_scaling_t_rel_times_D", N, "BDF",
              "|t_rel(D) D - t_rel(1)| / t_rel(1)", scale_err, TOL["T6_uniform_D_time_scaling_rel_max"], "<=")
    return rows, results


# ---------------------------------------------------------------- T8
def energy_run(N, beta, kind="mu", x_fun=ic, t_grid=None):
    dx, x = model.grid(N, L)
    phi = model.phi_profile(x)
    D = model.D_field(phi, 1.0, "const")
    s = solver.make_setup(N, phi, D, beta, dx, kind)
    if t_grid is None:
        t_grid = np.linspace(0.0, TIME["t_free_energy_horizon"], int(round(TIME["t_free_energy_horizon"] / TIME["save_dt_free_energy"])) + 1)
    run = solver.run_bdf(s, x_fun(x), t_grid, rtol=INT["rtol_primary"], atol=INT["atol_primary"])
    F = M.energy_series(run["C"], phi, beta, dx)
    return {"t": run["t"], "C": run["C"], "F": F, "phi": phi, "dx": dx, "D": D, "beta": beta, "run": run}


def T8():
    rows = []
    out = {}
    for beta in (PAR["beta_chi_over_RT"]["A_positive"], PAR["beta_chi_over_RT"]["B_negative"]):
        for N in GEO["N_list_convergence"]:
            R = energy_run(N, beta)
            dF = np.diff(R["F"])
            check(rows, "T8", f"max_positive_F_increment_beta{beta}_N{N}", N, "BDF", "max positive increment",
                  float(max(0.0, dF.max())), TOL["T8a_max_positive_F_increment_abs_max"], "<=")
            out[(beta, N)] = R
    # energy identity: integral of -dissipation over [0, 2] equals dF
    N = GEO["N_main"]
    beta = PAR["beta_chi_over_RT"]["A_positive"]
    # AMD-2: identity evaluated on a graded time grid that resolves the initial transient
    t_id = np.concatenate([[0.0], np.geomspace(1e-5, 0.1, 400), np.linspace(0.1, TIME["t_free_energy_horizon"], 2000)[1:]])
    R = energy_run(N, beta, t_grid=t_id)
    diss = np.array([model.dissipation_mu(c, R["phi"], beta, R["D"], R["dx"]) for c in R["C"]])
    lhs = R["F"][-1] - R["F"][0]
    rhs_int = -np.trapezoid(diss, R["t"])
    rel = abs(lhs - rhs_int) / max(abs(lhs), 1e-6)
    check(rows, "T8", "energy_identity_rel_residual", N, "BDF", "|dF - int(-diss)| / |dF|", rel,
          TOL["T8b_energy_identity_rel_max"], "<=")
    out["identity"] = {"dF": float(lhs), "int_dissipation": float(rhs_int), "rel": float(rel)}
    return rows, out


def T8c_exploratory():
    """Fick (F0-literal) flux free-energy trace with the non-symmetric IC cos(pi x). No verdict."""
    N = GEO["N_main"]
    beta = PAR["beta_chi_over_RT"]["A_positive"]
    dx, x = model.grid(N, L)
    phi = model.phi_profile(x)
    D = model.D_field(phi, 1.0, "const")
    t_grid = np.linspace(0.0, TIME["t_free_energy_horizon"], int(round(TIME["t_free_energy_horizon"] / TIME["save_dt_free_energy"])) + 1)
    s = solver.make_setup(N, phi, D, beta, dx, "fick")
    run = solver.run_bdf(s, 1.0 + 0.5 * np.cos(np.pi * x), t_grid, rtol=INT["rtol_primary"], atol=INT["atol_primary"])
    F = M.energy_series(run["C"], phi, beta, dx)
    dF = np.diff(F)
    return {"t": run["t"], "F": F, "max_positive_increment": float(max(0.0, dF.max())),
            "n_increases": int(np.sum(dF > 0)), "success": run["success"]}


# ---------------------------------------------------------------- T9 (read-only comparison with V0)
def T9():
    rows = []
    import genesis.diagnostics.vessel_permeability as vp  # read-only comparator; never used by model/solver

    Nslab = GEO["N_slab_T9_index_units"]
    w = GEO["width_slab_T9_index_units"]
    beta = 0.5
    i_idx = np.arange(Nslab)
    x_slab = i_idx + 0.5                       # index-unit cell centres (dx = 1)
    x0_slab = Nslab / 2.0
    phi1 = np.tanh((x0_slab - x_slab) / w)
    phi3 = np.broadcast_to(phi1[:, None, None], (Nslab, 4, 4)).copy()
    c3 = np.ones((Nslab, 4, 4))
    n_steps = 40000
    dt = 0.1
    for _ in range(n_steps):
        c3 = vp.relax_step(c3, phi3, beta, D=1.0, dt=dt, RT=1.0)   # existing V0 (read-only)
    c_ex = c3[:, 1, 1]
    # independent 1-D model, same geometry in index units (dx = 1), BDF to t = n_steps*dt
    dx = 1.0
    D = np.ones(Nslab)
    s = solver.make_setup(Nslab, phi1, D, beta, dx, "mu")
    run = solver.run_bdf(s, np.ones(Nslab), [0.0, n_steps * dt], rtol=INT["rtol_primary"], atol=INT["atol_primary"])
    c_mine = run["C"][-1]
    rel = float(np.max(np.abs(c_ex - c_mine) / c_mine))
    check(rows, "T9", "slab_equilibrium_vs_existing_rel", Nslab, "BDF vs existing SG (explicit dt=0.1)",
          "max rel diff", rel, TOL["T9_slab_vs_existing_equilibrium_rel_max"], "<=")
    cv_ex = float(vp.boltzmann_invariant_cv(c3, phi3, beta))
    check(rows, "T9", "existing_slab_boltzmann_cv", Nslab, "existing SG", "CV(c exp(beta phi))", cv_ex,
          1e-2, "<=")
    # transient comparison: informational (explicit Euler dt=0.1 vs BDF; not a pass/fail)
    t_chk = 0.5
    n_chk = int(round(t_chk / dt))
    c3_t = np.ones((Nslab, 4, 4))
    for _ in range(n_chk):
        c3_t = vp.relax_step(c3_t, phi3, beta, D=1.0, dt=dt, RT=1.0)
    run_t = solver.run_bdf(s, np.ones(Nslab), [0.0, n_chk * dt], rtol=INT["rtol_primary"], atol=INT["atol_primary"])
    transient_diff = float(np.max(np.abs(c3_t[:, 1, 1] - run_t["C"][-1])))
    return rows, {"c_existing": c_ex, "c_mine": c_mine, "x_slab": x_slab, "transient_diff_informational": transient_diff,
                  "t_check_transient": n_chk * dt}


# ---------------------------------------------------------------- T10
def T10():
    rows = []
    out = {}
    t_chk = [0.0, TIME["t_check"]]
    Nref = GEO["N_reference_T10"]
    # (a) spatial
    dxr, xr = model.grid(Nref, L)
    phir = model.phi_profile(xr)
    sr = solver.make_setup(Nref, phir, model.D_field(phir, 1.0, "const"), 0.5, dxr, "mu")
    ref = solver.run_bdf(sr, ic(xr), t_chk, rtol=INT["rtol_reference"], atol=INT["atol_reference"])
    cref = ref["C"][-1]
    errs = {}
    for N in GEO["N_list_convergence"]:
        dx, x = model.grid(N, L)
        phi = model.phi_profile(x)
        s = solver.make_setup(N, phi, model.D_field(phi, 1.0, "const"), 0.5, dx, "mu")
        r = solver.run_bdf(s, ic(x), t_chk, rtol=INT["rtol_primary"], atol=INT["atol_primary"])
        cavg = M.coarse_average(cref, Nref // N)
        errs[N] = M.L1_cell_error(r["C"][-1], cavg, dx)
        out[f"N{N}"] = {"err_L1": errs[N], "C": r["C"][-1], "x": x}
    p1 = M.observed_order(errs[64], errs[128])
    p2 = M.observed_order(errs[128], errs[256])
    order_row(rows, "T10", "spatial_order_64_128", "observed order", p1,
              TOL["T10a_observed_order_min_PASS"], TOL["T10a_observed_order_min_INCONCLUSIVE"], 128, "BDF")
    order_row(rows, "T10", "spatial_order_128_256", "observed order", p2,
              TOL["T10a_observed_order_min_PASS"], TOL["T10a_observed_order_min_INCONCLUSIVE"], 256, "BDF")
    monotone = errs[64] > errs[128] > errs[256]
    check(rows, "T10", "spatial_error_monotone_decreasing", 256, "BDF", "monotone (1=yes)", float(monotone), 1.0, ">=")
    out["spatial_errs"] = errs
    out["spatial_orders"] = (p1, p2)
    # (b) time tolerance at N=128
    N = GEO["N_main"]
    dx, x = model.grid(N, L)
    phi = model.phi_profile(x)
    s = solver.make_setup(N, phi, model.D_field(phi, 1.0, "const"), 0.5, dx, "mu")
    refb = solver.run_bdf(s, ic(x), t_chk, rtol=INT["rtol_reference"], atol=INT["atol_reference"])["C"][-1]
    terr = {}
    for rtol in INT["rtol_sequence_T10b"]:
        r = solver.run_bdf(s, ic(x), t_chk, rtol=rtol, atol=rtol * 1e-3)
        terr[rtol] = M.L1_cell_error(r["C"][-1], refb, dx)
    check(rows, "T10", "time_err_rtol1e-8_L1", N, "BDF", "L1 error", terr[1e-8],
          TOL["T10b_err_rtol1e-8_abs_max_L1"], "<=")
    check(rows, "T10", "time_err_decreasing_with_rtol", N, "BDF", "err(1e-8) < err(1e-6) (1=yes)",
          float(terr[1e-8] < terr[1e-6]), 1.0, ">=")
    out["time_errs"] = {str(k): v for k, v in terr.items()}
    # (c) RK4 time step at N=64 vs BDF reference (noise-floor rule AMD-1)
    N = 64
    dx, x = model.grid(N, L)
    phi = model.phi_profile(x)
    s = solver.make_setup(N, phi, model.D_field(phi, 1.0, "const"), 0.5, dx, "mu")
    refk = solver.run_bdf(s, ic(x), t_chk, rtol=INT["rtol_reference"], atol=INT["atol_reference"])["C"][-1]
    rk = {}
    for dt in INT["rk4_dt_sequence_T10c"]:
        cfin, _ = solver.run_rk4(s, ic(x), TIME["t_check"], dt)
        rk[dt] = M.L1_cell_error(cfin, refk, dx)
    dts = INT["rk4_dt_sequence_T10c"]
    e_hi, e_lo = rk[dts[0]], rk[dts[1]]
    floor = TOL["T10c_error_floor_L1"]
    if e_hi <= floor and e_lo <= floor:
        rows.append({"test_id": "T10", "case": "rk4_order_dt_2e-5_1e-5", "N": 64, "integrator": "RK4",
                     "metric": f"errors at floor (<= {floor}); order not measurable (AMD-1)",
                     "value": float("nan"), "threshold": floor, "op": "floor rule", "verdict": "INCONCLUSIVE"})
        p3 = float("nan")
    else:
        p3 = M.observed_order(e_hi, e_lo)
        order_row(rows, "T10", "rk4_order_dt_2e-5_1e-5", "observed order", p3,
                  TOL["T10c_rk4_order_min_PASS"], TOL["T10c_rk4_order_min_INCONCLUSIVE"], 64, "RK4")
    out["rk4_errs"] = {str(k): v for k, v in rk.items()}
    out["rk4_order"] = p3
    return rows, out


