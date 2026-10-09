"""Run the chemical lineage audit (v0.1) into a NEW output directory.

    python audits/chemical_lineage_v01/run_audit.py --out <new empty directory> [--smoke]

--smoke: small non-scored run (4 series, 5 generations) for implementation checks only (Phase 4).
Formal run: the defaults in PRE_REGISTRATION.json (24 series, 30 generations). Nothing is written into an existing
directory, and results/formal_v01 is never written by default. Thresholds come from PRE_REGISTRATION.json.
"""
import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import controls as C  # noqa: E402
import observers as O  # noqa: E402
import reaction_network as RN  # noqa: E402
import solver as S_  # noqa: E402
import species as SP  # noqa: E402
import statistics as ST  # noqa: E402
import strict_json as SJ  # noqa: E402
import thermodynamics as TH  # noqa: E402
import transfer_protocol as P  # noqa: E402

PRE = os.path.join(HERE, "PRE_REGISTRATION.json")
with open(PRE, encoding="utf-8") as fh:
    PR = json.load(fh)
PR.update(PR["statistics"])   # bootstrap / delta settings live under "statistics"
# The formal output is one new directory, results/formal_v01. Once written it is never overwritten: any
# non-empty target is refused, so the scored files are protected by that rule alone.
SCORED_DIR = os.path.join(HERE, "results", "formal_v01")


class OutputRefused(Exception):
    pass


def resolve_output_dir(out):
    """New, writable output directory, or OutputRefused (same rules as the P10 audit, v0.1.2)."""
    if out is None:
        raise OutputRefused("refusing to run without --out (no default write location).")
    target = os.path.realpath(os.path.abspath(out))
    if os.path.exists(target):
        if not os.path.isdir(target):
            raise OutputRefused(f"refusing to overwrite an existing file: {target}")
        if os.listdir(target):
            raise OutputRefused(f"refusing to write into a non-empty existing directory: {target}")
    os.makedirs(target, exist_ok=True)
    return target


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True).stdout.strip()


# ------------------------------------------------------------------ core computation
def arm_suite(n_series, tau, f, n_gen):
    L1 = C.run_arm("L1", n_series, tau, f, n_gen)
    LR = C.run_arm("LR", n_series, tau, f, n_gen)
    LN = C.run_arm("LN", n_series, tau, f, n_gen)
    LS = C.run_arm("LS", n_series, tau, f, n_gen, donor_ends=L1)
    L0 = C.run_arm("L0", n_series, tau, f, n_gen)
    return {"L1": L1, "LR": LR, "LN": LN, "LS": LS, "L0": L0}


def ci(vals, pr):
    return ST.bootstrap_ci(vals, n_boot=pr["bootstrap_resamples"], seed=pr["bootstrap_seed"])


def summarise(arms, tau, f, n_gen, pr):
    """Series-level rows and generation summaries for one (tau, f)."""
    rows, summ = [], []
    L1, LR, LN, LS, L0 = arms["L1"], arms["LR"], arms["LN"], arms["LS"], arms["L0"]
    disp0 = O.per_series_dispersion(L1[:, 0])
    for g in range(n_gen + 1):
        disp_g = O.per_series_dispersion(L1[:, g])
        off_LR = O.per_series_offset(L1[:, g], LR[:, g])
        off_LS = O.per_series_offset(L1[:, g], LS[:, g])
        off_L0 = O.per_series_offset(L1[:, g], L0[:, g])
        disp_LN = O.per_series_dispersion(LN[:, g])
        passive = (f ** g) * disp0
        for s in range(L1.shape[0]):
            rows.append({"tau": tau, "f": f, "gen": g, "series": s,
                         "disp_L1": disp_g[s], "offset_L1_LR": off_LR[s], "offset_L1_LS": off_LS[s],
                         "offset_L1_L0": off_L0[s], "disp_LN": disp_LN[s], "passive_expectation": passive[s],
                         "complexed_fraction_L1": O.complexed_unit_fraction(L1[s, g])})
        m, lo, hi = ci(disp_g, pr)
        mo, lo_o, hi_o = ci(off_LR, pr)
        summ.append({"tau": tau, "f": f, "gen": g,
                     "disp_L1_mean": m, "disp_L1_lo": lo, "disp_L1_hi": hi,
                     "offset_L1_LR_mean": mo, "offset_L1_LR_lo": lo_o, "offset_L1_LR_hi": hi_o})
    return rows, summ


def verdicts_for(rows, tau, f, pr, n_gen):
    """Pre-registered decisions for one (tau, f). Uses series-level values only."""
    delta = pr["delta_abs"]
    def col(g, key):
        return np.array([r[key] for r in rows if r["gen"] == g and r["series"] >= 0])
    out = {}
    d1 = col(1, "disp_L1")
    d5 = col(5, "disp_L1")
    d0 = col(0, "disp_L1")
    pas1 = col(1, "passive_expectation")
    _, lo1, _ = ST.bootstrap_ci(d1, pr["bootstrap_resamples"], seed=pr["bootstrap_seed"])
    _, lo5, _ = ST.bootstrap_ci(d5, pr["bootstrap_resamples"], seed=pr["bootstrap_seed"])
    out["A_single_generation_carryover_present"] = bool(lo1 > delta)
    out["C_parent_specific_persistence_to_g5_present"] = bool(lo5 > delta)
    # two-level report: "detectable above numerical noise" is reported next to the meaningful threshold delta
    floor = pr["delta_noise_floor_abs"]
    out["A_detectable_above_noise_floor"] = bool(lo1 > floor)
    out["C_detectable_above_noise_floor"] = bool(lo5 > floor)
    ratio1, rlo1, rhi1 = ST.bootstrap_ratio_ci(d1, pas1, pr["bootstrap_resamples"], seed=pr["bootstrap_seed"])
    out["Q2_excess_over_passive_at_g1"] = "EXCESS" if rlo1 > 1.0 else ("BELOW_PASSIVE" if rhi1 < 1.0 else "NOT_DISTINGUISHABLE_FROM_PASSIVE")
    out["R_passive_ratio_g1"] = [ratio1, rlo1, rhi1]
    off30 = col(n_gen, "offset_L1_LR")
    _, olo30, _ = ST.bootstrap_ci(off30, pr["bootstrap_resamples"], seed=pr["bootstrap_seed"])
    d30 = col(n_gen, "disp_L1")
    _, dlo30, _ = ST.bootstrap_ci(d30, pr["bootstrap_resamples"], seed=pr["bootstrap_seed"])
    out["shared_offset_at_final_gen_present"] = bool(olo30 > delta)
    out["parent_specific_at_final_gen_present"] = bool(dlo30 > delta)
    donor1 = col(1, "offset_L1_LS")
    _, dnlo, _ = ST.bootstrap_ci(donor1, pr["bootstrap_resamples"], seed=pr["bootstrap_seed"])
    out["donor_identity_effect_at_g1_present"] = bool(dnlo > delta)
    return out


# ------------------------------------------------------------------ invariant checks (inside the run)
def invariant_block(arms, tau, f, n_gen, pr):
    """Mass ledger, detailed balance, free-energy monotonicity on a sampled closed phase, negative-value screen."""
    res = {}
    L1 = arms["L1"]
    res["max_element_residual_end_states"] = float(np.max(np.abs(np.array(
        [SP.element_totals(L1[s, g]) - 1.0 for s in range(L1.shape[0]) for g in range(n_gen + 1)]))))
    res["min_concentration_L1"] = float(np.min(L1))
    res["negative_below_tolerance_fail"] = bool(np.min(L1) < -pr["negative_tolerance"])
    res["min_concentration_in_roundoff_band"] = bool(np.min(L1) < 0 and np.min(L1) >= -pr["negative_tolerance"])
    # detailed balance: equilibrium of a long closed run satisfies Q_r = K_r
    kf, kr = TH.forward_reverse_rates()
    eq = S_.end_state(P.fresh_material(0.0), 300.0, kf, kr)
    Q = np.array([np.prod(np.power(eq[:, None], RN.MP), axis=0)])[0] / np.prod(np.power(eq[:, None], RN.MR), axis=0)
    res["detailed_balance_max_log_error"] = float(np.max(np.abs(np.log(Q) - np.log(TH.equilibrium_constants()))))
    res["wegscheider_residual"] = TH.wegscheider_residual()
    res["conservation_residual_network"] = RN.conservation_residual()
    # free energy: sample the closed phase of one L1 generation (series 0, generation 1 start)
    start, _ = P.start_of_generation(L1[0, 0], f, "L1")
    tgrid = np.linspace(0.0, tau, 41)
    _, Cgrid = S_.integrate(start, tau, kf, kr, t_eval=tgrid)
    G = np.array([TH.free_energy(c) for c in Cgrid])
    res["free_energy_max_increase_in_closed_phase"] = float(np.max(np.diff(G)))
    res["free_energy_monotone_tolerance"] = pr["free_energy_increase_tolerance"]
    res["free_energy_monotone_pass"] = bool(np.max(np.diff(G)) <= pr["free_energy_increase_tolerance"])
    return res


def ssa_block(pr):
    """T15: one-reaction cross-check of X + Y <-> XY, ODE vs exact Gillespie (independent random streams)."""
    kf_all, kr_all = TH.forward_reverse_rates()
    kf, kr = float(kf_all[0]), float(kr_all[0])      # X+Y <-> XY is reaction 0
    omega, n_runs, t_end = pr["ssa"]["omega"], pr["ssa"]["runs"], pr["ssa"]["t_end"]
    c0 = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 0.0])          # X, Y only: other reactions are inert
    _, Code = S_.integrate(c0, t_end, kf_all, kr_all)
    ode_xy = Code[-1, SP.IDX["XY"]]
    rng = np.random.default_rng(pr["ssa"]["seed"])
    vals = np.empty(n_runs)
    for i in range(n_runs):
        _, _, nxy = S_.gillespie_xy(int(omega), int(omega), 0, omega, kf, kr, t_end, rng)
        vals[i] = nxy / omega
    mean, se = vals.mean(), vals.std(ddof=1) / np.sqrt(n_runs)
    return {"ode_XY": float(ode_xy), "ssa_mean_XY": float(mean), "ssa_se": float(se),
            "abs_difference": float(abs(mean - ode_xy)),
            "pass": bool(abs(mean - ode_xy) <= pr["ssa"]["sigma_multiplier"] * se + pr["ssa"]["absolute_floor"])}


def convergence_block(pr):
    """T14: ODE tolerance sequence on one lineage (smoke scale), L1, tau = 2, f = 0.1."""
    kf, kr = TH.forward_reverse_rates()
    start = C.seed_state(0)
    end = {}
    for rt in pr["integrators"]["rtol_sequence_T14"]:
        _, Cg = S_.integrate(start, 2.0, kf, kr, rtol=rt, atol=rt * 1e-3)
        end[rt] = Cg[-1]
    seq = pr["integrators"]["rtol_sequence_T14"]
    e_coarse = float(np.max(np.abs(end[seq[0]] - end[seq[-1]])))
    e_mid = float(np.max(np.abs(end[seq[1]] - end[seq[-1]])))
    return {"max_abs_diff_coarse_vs_finest": e_coarse, "max_abs_diff_mid_vs_finest": e_mid,
            "pass": bool(e_mid <= e_coarse and e_mid <= pr["integrators"]["convergence_tolerance"])}


# ------------------------------------------------------------------ main
def main(outdir, smoke):
    t0 = time.time()
    pr = PR
    n_series = 4 if smoke else pr["design"]["n_series"]
    n_gen = 5 if smoke else pr["design"]["n_generations"]
    taus = [2.0] if smoke else pr["design"]["tau_values"]
    fs = [0.10] if smoke else pr["design"]["f_values"]
    all_rows, all_summ, verdicts, inv = [], [], {}, {}
    for tau in taus:
        for f in fs:
            arms = arm_suite(n_series, tau, f, n_gen)
            rows, summ = summarise(arms, tau, f, n_gen, pr)
            all_rows += rows
            all_summ += summ
            verdicts[f"tau={tau},f={f}"] = verdicts_for(rows, tau, f, pr, n_gen)
            inv[f"tau={tau},f={f}"] = invariant_block(arms, tau, f, n_gen, pr)
    ssa = ssa_block(pr)
    conv = convergence_block(pr)

    def write_csv(name, rows):
        if not rows:
            return
        with open(os.path.join(outdir, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)
    write_csv("series_level.csv", all_rows)
    write_csv("generation_summary.csv", all_summ)

    summary = {"audit_id": pr["audit_id"], "version": pr["version"], "smoke": smoke,
               "design": {"n_series": n_series, "n_generations": n_gen, "tau_values": taus, "f_values": fs},
               "verdicts": verdicts, "invariants": inv, "T15_ssa_cross_check": ssa,
               "T14_convergence": conv, "wall_clock_s": round(time.time() - t0, 1)}
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as fh:
        fh.write(SJ.dumps(SJ.finalize_summary(summary), ensure_ascii=False, indent=2) + "\n")

    manifest = {"audit_id": pr["audit_id"], "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                "head_commit_at_run": git("rev-parse", "HEAD"),
                "base_main_commit": pr["base_commit"],
                "pre_registration_sha256": sha256_file(PRE),
                "code_sha256": {f: sha256_file(os.path.join(HERE, f)) for f in
                                ["species.py", "reaction_network.py", "thermodynamics.py", "solver.py",
                                 "transfer_protocol.py", "controls.py", "observers.py", "statistics.py",
                                 "run_audit.py", "visualize.py"]},
                "python": platform.python_version(), "numpy": np.__version__,
                "scipy": __import__("scipy").__version__, "platform": platform.platform(),
                "smoke": smoke, "output_dir": os.path.relpath(outdir, REPO), "executed_at_unix": int(time.time())}
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as fh:
        fh.write(SJ.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    try:
        import visualize
        visualize.make_all(all_summ, all_rows, inv, outdir)
        figs = "written"
    except Exception as exc:
        figs = f"FAILED: {type(exc).__name__}: {exc}"
    print("verdicts:", json.dumps(verdicts, ensure_ascii=False, indent=1))
    print("T15 SSA:", ssa)
    print("T14 convergence:", conv)
    print("figures:", figs)
    print("wall clock s:", round(time.time() - t0, 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Chemical lineage audit (v0.1): writes into a NEW directory only.")
    ap.add_argument("--out", default=None, help="new empty output directory (required)")
    ap.add_argument("--smoke", action="store_true", help="small non-scored implementation check")
    args = ap.parse_args()
    try:
        target = resolve_output_dir(args.out)
    except OutputRefused as exc:
        print("REFUSED:", exc, file=sys.stderr)
        sys.exit(2)
    print("writing run to", target)
    main(target, args.smoke)
