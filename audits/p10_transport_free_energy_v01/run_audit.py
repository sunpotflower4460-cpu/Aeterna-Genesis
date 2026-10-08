"""Run the full P10 transport audit (v0.1) and write results/.

Usage (from the repository root):
    python audits/p10_transport_free_energy_v01/run_audit.py

Writes: results/numerical_results.csv, results/summary.json, results/manifest.json,
        results/test_results.json (pytest run of this audit's tests), results/figures/*.png.
Thresholds come only from PRE_REGISTRATION.json. Nothing here edits the model to pass a test.
"""
import csv
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import scenarios as S  # noqa: E402
import model  # noqa: E402
import metrics as M  # noqa: E402

RES = os.path.join(HERE, "results")
FIG = os.path.join(RES, "figures")
os.makedirs(FIG, exist_ok=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True).stdout.strip()


def main():
    t0 = time.time()
    rows = []

    # T1
    rows += S.T1()

    # T2
    r2, d2 = S.T2()
    rows += r2

    # T3 (+ sharp)
    r3, d3 = S.T3()
    rows += r3

    # T4
    r4, d4 = S.T4()
    rows += r4

    # T5
    r5, d5 = S.T5()
    rows += r5

    # T6
    r6, d6 = S.T6()
    rows += r6

    # T8 (energy) — also provides runs for T7
    r8, d8 = S.T8()
    rows += r8
    exp8 = S.T8c_exploratory()

    # T7: structural boundary checks + positivity/finiteness/mass over every saved run in T2,T3,T4,T8
    S.boundary_structure_check(rows)
    series = []
    series.append(("T2_A_fick", d2["A_run"]["run"]["C"], d2["A_run"]["dx"]))
    series.append(("T2_B_mu", d2["B_run"]["run"]["C"], d2["B_run"]["dx"]))
    for N in (64, 128, 256):
        series.append((f"T3_N{N}", d3[N]["run"]["C"], d3[N]["dx"]))
    series.append(("T4_A", d4["RA"]["run"]["C"], d4["RA"]["dx"]))
    series.append(("T4_B", d4["RB"]["run"]["C"], d4["RB"]["dx"]))
    for key, R in d8.items():
        if isinstance(key, tuple):
            series.append((f"T8_beta{key[0]}_N{key[1]}", R["C"], R["dx"]))
    for name, C, dx in series:
        M0 = 1.0
        fin, cmin = M.finite_and_positive(C)
        rows.append({"test_id": "T7", "case": name, "N": C.shape[1], "integrator": "BDF",
                     "metric": "mass_residual_rel_max", "value": M.mass_residual_rel(C, dx, M0),
                     "threshold": S.TOL["T7_mass_residual_rel_max"], "op": "<=",
                     "verdict": "PASS" if M.mass_residual_rel(C, dx, M0) <= S.TOL["T7_mass_residual_rel_max"] else "FAIL"})
        rows.append({"test_id": "T7", "case": name, "N": C.shape[1], "integrator": "BDF",
                     "metric": "min_c_strictly_positive", "value": cmin, "threshold": 0.0, "op": ">",
                     "verdict": "PASS" if (fin and cmin > 0.0) else "FAIL"})

    # T9 (read-only comparison with existing V0)
    r9, d9 = S.T9()
    rows += r9

    # T10 (convergence)
    r10, d10 = S.T10()
    rows += r10

    # exploratory: no verdict
    rows.append({"test_id": "T8c", "case": "fick_flux_F_trace_cos_pi_x", "N": 128, "integrator": "BDF",
                 "metric": "max positive F increment (EXPLORATORY, no verdict)",
                 "value": exp8["max_positive_increment"], "threshold": float("nan"), "op": "exploratory",
                 "verdict": "EXPLORATORY"})
    rows.append({"test_id": "T8c", "case": "fick_flux_F_trace_cos_pi_x", "N": 128, "integrator": "BDF",
                 "metric": "number of saved steps with F increase (EXPLORATORY)",
                 "value": exp8["n_increases"], "threshold": float("nan"), "op": "exploratory",
                 "verdict": "EXPLORATORY"})

    # existing V0 suite: baseline read-only run
    v0 = subprocess.run([sys.executable, "-m", "pytest", "tests/test_vessel_permeability.py", "-q", "-p",
                         "no:cacheprovider"], cwd=REPO, capture_output=True, text=True)
    v0_tail = v0.stdout.strip().splitlines()[-1] if v0.stdout.strip() else ""
    v0_tail = re.sub(r" in [0-9.]+s", "", v0_tail)   # wall-clock time is not a result; keep the record deterministic
    rows.append({"test_id": "T9", "case": "existing_V0_suite_read_only", "N": "", "integrator": "pytest",
                 "metric": "existing tests/test_vessel_permeability.py: " + v0_tail, "value": float(v0.returncode == 0),
                 "threshold": 1.0, "op": "==", "verdict": "PASS" if v0.returncode == 0 else "FAIL"})

    # ------------------------------------------------------------- write CSV
    fields = ["test_id", "case", "N", "integrator", "metric", "value", "threshold", "op", "verdict"]
    with open(os.path.join(RES, "numerical_results.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

    # ------------------------------------------------------------- verdict per test
    tids = sorted({r["test_id"] for r in rows if r["verdict"] in ("PASS", "FAIL", "INCONCLUSIVE")})
    rank = {"PASS": 0, "INCONCLUSIVE": 1, "FAIL": 2}
    tv = {}
    for tid in tids:
        vs = [r["verdict"] for r in rows if r["test_id"] == tid and r["verdict"] in rank]
        tv[tid] = max(vs, key=lambda v: rank[v])
    n_rows = {tid: sum(1 for r in rows if r["test_id"] == tid) for tid in tids}
    n_fail = {tid: sum(1 for r in rows if r["test_id"] == tid and r["verdict"] == "FAIL") for tid in tids}
    n_inc = {tid: sum(1 for r in rows if r["test_id"] == tid and r["verdict"] == "INCONCLUSIVE") for tid in tids}

    # numeric headline values for the report
    headline = {
        "T2_fick_ratio": d2["A_ratio"], "T2_B_ratio_measured": d2["B_ratio"], "T2_B_ratio_predicted": d2["B_pred"],
        "T3_ratio_measured_N128": d3[128]["ratio_meas"], "T3_ratio_predicted_discrete_N128": d3[128]["ratio_disc"],
        "T3_ratio_predicted_continuum_N128": d3[128]["ratio_cont"],
        "T3_continuum_rel_error_by_N": {str(k): v for k, v in d3["cont_err"].items()},
        "T3_sharp_ratio_measured": d3["sharp"]["ratio_meas"], "T3_sharp_ratio_predicted": d3["sharp"]["ratio_disc"],
        "T4_ratio_A": d4["rA"], "T4_ratio_B": d4["rB"], "T4_S_B_over_A": d4["S"],
        "T6_relaxation_times": {k: v["t_rel"] for k, v in d6.items()},
        "T8_identity": d8["identity"],
        "T8_max_positive_increment_by_case": {f"beta{k[0]}_N{k[1]}": float(max(0.0, np.diff(v["F"]).max()))
                                             for k, v in d8.items() if isinstance(k, tuple)},
        "T8c_fick_max_positive_increment": exp8["max_positive_increment"], "T8c_fick_n_increases": exp8["n_increases"],
        "T9_slab_max_rel_diff": float(np.max(np.abs(d9["c_existing"] - d9["c_mine"]) / d9["c_mine"])),
        "T9_transient_diff_informational": d9["transient_diff_informational"],
        "T10_spatial_errors": d10["spatial_errs"], "T10_spatial_orders": list(d10["spatial_orders"]),
        "T10_time_errors": d10["time_errs"], "T10_rk4_errors": d10["rk4_errs"], "T10_rk4_order": d10["rk4_order"],
    }

    summary = {
        "audit_id": S.P["audit_id"], "version": S.P["version"], "role": S.P["role"],
        "test_verdicts": tv, "rows_per_test": n_rows, "fail_rows_per_test": n_fail, "inconclusive_rows_per_test": n_inc,
        "overall": ("PASS" if all(v == "PASS" for v in tv.values()) else
                    ("FAIL" if any(v == "FAIL" for v in tv.values()) else "INCONCLUSIVE")),
        "headline": headline,
        "wall_clock_s": round(time.time() - t0, 1),
    }
    with open(os.path.join(RES, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))

    # ------------------------------------------------------------- figures
    try:
        import visualize
        visualize.make_all(d2, d3, d4, d6, d8, exp8, FIG)
        fig_status = "written"
    except Exception as exc:  # recorded, never silently dropped
        fig_status = f"FAILED: {type(exc).__name__}: {exc}"

    # ------------------------------------------------------------- pytest of this audit
    junit = os.path.join(RES, "_pytest_junit.xml")
    pt = subprocess.run([sys.executable, "-m", "pytest", os.path.join(HERE, "tests"), "-q", "-p", "no:cacheprovider",
                         f"--junitxml={junit}"], cwd=REPO, capture_output=True, text=True)
    pt_summary = pt.stdout.strip().splitlines()[-1] if pt.stdout.strip() else ""
    import xml.etree.ElementTree as ET
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    cases = []
    if os.path.exists(junit):
        root = ET.parse(junit).getroot()
        for suite in root.iter("testsuite"):
            for k in counts:
                counts[k] += int(suite.attrib.get(k, 0))
        for tc in root.iter("testcase"):
            status = "passed"
            for child in tc:
                if child.tag in ("failure", "error", "skipped"):
                    status = child.tag
            cases.append({"classname": tc.attrib.get("classname"), "name": tc.attrib.get("name"), "status": status,
                          "time_s": float(tc.attrib.get("time", 0.0))})
        os.remove(junit)
    test_results = {"command": "python -m pytest audits/p10_transport_free_energy_v01/tests -q",
                    "returncode": pt.returncode, "summary_line": pt_summary, "counts": counts, "cases": cases}
    with open(os.path.join(RES, "test_results.json"), "w", encoding="utf-8") as fh:
        json.dump(test_results, fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------- manifest
    code_files = ["model.py", "solver.py", "metrics.py", "scenarios.py", "run_audit.py", "visualize.py",
                  "PRE_REGISTRATION.json"] + [os.path.join("tests", f) for f in sorted(os.listdir(os.path.join(HERE, "tests")))
                                             if f.endswith(".py")]
    import scipy
    manifest = {
        "base_commit": S.P["base_commit"],
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "head_commit_at_run": git("rev-parse", "HEAD"),
        "prereg_commit": git("log", "-1", "--format=%H", "--", "audits/p10_transport_free_energy_v01/PRE_REGISTRATION.json"),
        "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
        "platform": platform.platform(),
        "sha256_code_and_prereg": {f: sha256(os.path.join(HERE, f)) for f in code_files},
        "sha256_protected_sources_at_run": {
            p: sha256(os.path.join(REPO, p)) for p in [
                "docs/frontier/F0_P10_active_vessel.md", "genesis/diagnostics/vessel_permeability.py",
                "tests/test_vessel_permeability.py", "AGENTS.md"]},
        "executed_at_unix": int(time.time()),
        "wall_clock_s": round(time.time() - t0, 1),
        "figure_status": fig_status,
    }
    with open(os.path.join(RES, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print("overall:", summary["overall"])
    for tid in tids:
        print(f"  {tid}: {tv[tid]}  (rows={n_rows[tid]}, FAIL={n_fail[tid]}, INCONCLUSIVE={n_inc[tid]})")
    print("pytest:", pt_summary)
    print("figures:", fig_status)


if __name__ == "__main__":
    main()
