#!/usr/bin/env python3
"""Aeterna-Genesis e008 -- co-emergence: matter, time, space from one white field.

================================ AUDIT HEADER ================================
MODULE:      e008_coemergence
QUESTION:    From one white start (uniform + noise) and ONE local law (GPE),
             do matter (phase defects), time (an arrow + reversibility echo) and
             space (a correlation length / folding) co-emerge -- none put in?
PUT IN:      damped GPE  d psi/dt = -(i+gamma)(-1/2 lap + g|psi|^2 - mu)psi
             + white initial condition (psi = small complex Gaussian noise)
             + a quench (mu ramped from <0 to >0 over time tau_Q).
             For the echo, gamma=0 (conservative GPE). No vortex / arrow /
             geometry is ever written in. THIS ONLY.
EMERGED:     (measured) Kibble-Zurek vortices nucleate from noise with a density
             power law N ~ tau_Q^{-b}; net winding ~ 0 (balanced +/-); a
             coarsening arrow (N falls, inter-defect spacing grows) that is
             ABSENT under the reversible (gamma=0) law; a growing length scale.
CLAIM TIER:  measured (defect count, KZ exponent b, net winding 0, quantization,
             coarsening spacing, echo fidelity) ; interpretive ("time-space-
             matter co-emergence", arrow-from-dissipation lesson) ;
             frontier (entanglement (RT) geometry, background-free).
KNOWN MATCH: Kibble-Zurek (quench -> defect density ~ tau_Q^{-power}, seen in
             BEC); cosmic strings / superfluid vortices; coarsening dynamics;
             Loschmidt echo; e001-e003 (vortices, rings).
AUDIT (7):   see AUDIT.md.
STATUS:      (filled by run)
A_OR_B:      (A) faithful emergence. Hand input = the field law + a white start.
             The background (fixed lattice = space) is GIVEN ((B) not attempted).

HONEST FLOORS (LAW.md, stated up front):
  * FIXED LATTICE: space is GIVEN. The "geometry" here is a correlation /
    folding length, NOT entanglement (Ryu-Takayanagi) geometry. The quantum
    route (e005-e007) is the complementary half; the bridge is frontier.
  * "matter+time+space co-emergence" is the INTERPRETIVE reading; the measured
    facts are each emergence separately + the KZ numbers.
  * gamma>0 (damping) is a coarse-graining/dissipation; the coarsening arrow
    needs it. The reversible law (gamma=0) shows the arrow is NOT in the law
    (echo). KZ exponent b is protocol-dependent (gamma, count threshold).
=============================================================================

Run with no args for the full result + result.json. --quick for a short run.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core import field, measure, vortex  # noqa: E402
from core.fft import k_squared  # noqa: E402

DEFAULT = {
    "L": 192, "g": 1.0, "mu_i": -1.0, "mu_f": 1.0, "dt": 0.05, "gamma": 0.3,
    "noise": 0.05, "hold": 400, "frac": 0.1,
    "tauQ_list": [50, 100, 200, 400, 800, 1600],
    "seeds": [1, 2, 3],
}
QUICK = {"L": 128, "tauQ_list": [50, 100, 200, 400], "seeds": [1, 2], "hold": 300}


def quench(L, g, mu_i, mu_f, tauQ, hold, dt, gamma, noise, seed):
    """Damped GPE quench from white noise. Returns the final field psi."""
    rng = np.random.default_rng(seed)
    k2 = k_squared(L)
    V = np.zeros((L, L))
    psi = noise * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
    for s in range(tauQ + hold):
        mu = mu_i + (mu_f - mu_i) * min(1.0, s / tauQ)
        psi = field.step_damped_2d(psi, V, k2, g, mu, dt, gamma)
    return psi


def kz_scaling(p, seeds, tauQ_list):
    """Sweep quench time -> defect count -> KZ power law N ~ tauQ^{-b}."""
    rows = []
    for tauQ in tauQ_list:
        ns, nets, rhos = [], [], []
        for seed in seeds:
            psi = quench(p["L"], p["g"], p["mu_i"], p["mu_f"], tauQ, p["hold"],
                         p["dt"], p["gamma"], p["noise"], seed)
            n, net = vortex.count_defects(psi, frac=p["frac"])
            ns.append(n)
            nets.append(net)
            rhos.append(float(np.median(np.abs(psi) ** 2)))
        rows.append({"tauQ": tauQ, "N_mean": float(np.mean(ns)),
                     "N_std": float(np.std(ns)), "N_seeds": ns,
                     "net_winding_absmean": float(np.mean(np.abs(nets))),
                     "rho_median": float(np.mean(rhos))})
    taus = np.array([r["tauQ"] for r in rows], float)
    nd = np.array([r["N_mean"] for r in rows], float)

    def _fit(mask):
        b, loga = np.polyfit(np.log(taus[mask]), np.log(nd[mask]), 1)
        pred = np.exp(loga + b * np.log(taus[mask]))
        sr = np.sum((np.log(nd[mask]) - np.log(pred)) ** 2)
        st = np.sum((np.log(nd[mask]) - np.log(nd[mask]).mean()) ** 2)
        return float(-b), float(1.0 - sr / st) if st > 0 else float("nan")

    # KZ has a fast-quench SATURATION knee (finite max defect density): a single
    # power law does not cover it. Fit the slow-quench power-law regime (upper
    # half of tau_Q) and separately flag the saturation as an emergent feature.
    n = len(taus)
    if n < 3:
        raise ValueError("kz_scaling needs >=3 tau_Q values for a meaningful "
                         "slow-regime power-law fit (got %d)" % n)
    slow = np.arange(n) >= max(1, n // 2 - 1)        # drop the saturated tail
    b_slow, r2_slow = _fit(slow)
    b_all, r2_all = _fit(np.ones(n, bool))
    # saturation: at the fastest quench N is below the power-law extrapolation
    saturates = bool(nd[0] < np.exp(np.polyfit(np.log(taus[slow]),
                     np.log(nd[slow]), 1)[1] + (-b_slow) * np.log(taus[0])) * 0.92)
    extra = {"b_all_range": b_all, "r2_all_range": r2_all,
             "fast_quench_saturates": saturates}
    return rows, b_slow, r2_slow, extra


def coarsening(p, tauQ, seed=1, samples=12):
    """Post-quench: N(t) decreases, inter-defect spacing L/sqrt(N) grows (arrow)."""
    L, g = p["L"], p["g"]
    k2 = k_squared(L)
    V = np.zeros((L, L))
    rng = np.random.default_rng(seed)
    psi = p["noise"] * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
    # ramp
    for s in range(tauQ):
        mu = p["mu_i"] + (p["mu_f"] - p["mu_i"]) * (s / tauQ)
        psi = field.step_damped_2d(psi, V, k2, g, mu, p["dt"], p["gamma"])
    # coarsen at mu_f, sample N and spacing
    Ns, spac = [], []
    every = 150
    for s in range(samples * every):
        psi = field.step_damped_2d(psi, V, k2, g, p["mu_f"], p["dt"], p["gamma"])
        if s % every == 0:
            n, _ = vortex.count_defects(psi, frac=p["frac"])
            Ns.append(n)
            spac.append(L / np.sqrt(max(n, 1)))
    spac = np.asarray(spac)
    return {"N_t": Ns, "spacing_t": [round(float(x), 3) for x in spac],
            "spacing_grows": bool(spac[-1] > spac[0]),
            "N_decreases": bool(Ns[-1] < Ns[0])}


def echo(p, tstar=600, seed=1):
    """Conservative (gamma=0) reversibility: forward t*, conjugate, forward t*.

    Returns the overlap fidelity with the start. ~1 means the law is reversible
    -- the arrow is NOT in the law (it needs the coarse-graining / dissipation).
    """
    L, g, mu = p["L"], p["g"], p["mu_f"]
    k2 = k_squared(L)
    V = np.zeros((L, L))
    rng = np.random.default_rng(seed)
    psi = p["noise"] * (rng.standard_normal((L, L)) + 1j * rng.standard_normal((L, L)))
    psi0 = psi.copy()
    dt = 0.02
    for _ in range(tstar):
        psi = field.step_real(psi, V, k2, g, mu, dt)
    psi = np.conj(psi)                      # time reversal for the GPE
    for _ in range(tstar):
        psi = field.step_real(psi, V, k2, g, mu, dt)
    psi = np.conj(psi)
    num = np.abs(np.vdot(psi0, psi)) ** 2
    den = np.vdot(psi0, psi0).real * np.vdot(psi, psi).real
    if den <= 0.0:                          # zero field => fidelity undefined
        return float("nan")
    return float(num / den)


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows, b, r2, extra = kz_scaling(p, p["seeds"], p["tauQ_list"])
    coa = coarsening(p, tauQ=p["tauQ_list"][len(p["tauQ_list"]) // 2])
    fid = echo(p)
    net_abs = float(np.mean([r["net_winding_absmean"] for r in rows]))
    quantized = bool(vortex.is_circulation_quantized(
        quench(p["L"], p["g"], p["mu_i"], p["mu_f"], p["tauQ_list"][-1],
               p["hold"], p["dt"], p["gamma"], p["noise"], p["seeds"][0])))
    return {
        "params": p,
        "matter_kz": {"rows": rows, "kz_exponent_b": b, "kz_loglog_r2": r2,
                      "kz_saturation": extra,
                      "net_winding_absmean": net_abs,
                      "defects_mean": float(np.mean([r["N_mean"] for r in rows])),
                      "circulation_quantized": quantized},
        "time_arrow": {"coarsening": coa, "echo_fidelity": fid},
        "co_emergence": {
            "matter": "KZ vortices, N ~ tauQ^{-%.3f}, net winding ~0" % b,
            "time": "coarsening arrow (spacing grows) + reversible echo %.3f" % fid,
            "space": "emergent inter-defect length scale (correlation)",
            "tier": "measured(each) + interpretive(co-emergence reading)",
        },
    }


EXPECT = {"b_lo": 0.15, "b_hi": 0.9, "r2_min": 0.9,
          "net_over_sqrtN_max": 2.0, "echo_min": 0.99}


def evaluate(result, quick=False):
    m = result["matter_kz"]
    t = result["time_arrow"]
    # A balanced +/- defect gas has net winding of order sqrt(N), NOT N. So the
    # physically meaningful "balanced" test is net_abs / sqrt(N) ~ O(1), not an
    # arbitrary absolute constant (which is loose at large N). See review F7.
    defects_mean = m.get("defects_mean")
    if defects_mean is None:                # older result.json: derive from rows
        defects_mean = float(np.mean([r["N_mean"] for r in m["rows"]]))
    sqrtN = float(np.sqrt(max(defects_mean, 1.0)))
    net_balanced = (m["net_winding_absmean"] / sqrtN) < EXPECT["net_over_sqrtN_max"]
    checks = {
        "kz_power_law": EXPECT["b_lo"] < m["kz_exponent_b"] < EXPECT["b_hi"],
        "kz_loglog_clean": m["kz_loglog_r2"] > EXPECT["r2_min"],
        "net_winding_balanced": net_balanced,
        "circulation_quantized": m["circulation_quantized"],
        "coarsening_arrow": t["coarsening"]["spacing_grows"]
        and t["coarsening"]["N_decreases"],
        "reversible_echo": t["echo_fidelity"] > EXPECT["echo_min"],
    }
    return all(checks.values()), checks


def _print_report(result, quick=False):
    print(__doc__)
    m, t = result["matter_kz"], result["time_arrow"]
    print("---------------------------- MEASUREMENTS ----------------------------")
    print("[matter] Kibble-Zurek defects from white noise:")
    for r in m["rows"]:
        print("   tauQ=%5d  N=%6.1f +-%4.1f  net|w|=%.1f  rho_med=%.2f"
              % (r["tauQ"], r["N_mean"], r["N_std"],
                 r["net_winding_absmean"], r["rho_median"]))
    print("   KZ power law (slow-quench regime)  N ~ tauQ^(-%.3f)  (R^2=%.3f)"
          % (m["kz_exponent_b"], m["kz_loglog_r2"]))
    print("   fast-quench saturation (KZ knee): %s  (full-range b=%.3f)"
          % (m["kz_saturation"]["fast_quench_saturates"],
             m["kz_saturation"]["b_all_range"]))
    print("   net winding |<.>| = %.2f (balanced +/-)  quantized=%s"
          % (m["net_winding_absmean"], m["circulation_quantized"]))
    print("[time] arrow + echo:")
    print("   coarsening spacing: %s -> grows=%s, N decreases=%s"
          % (t["coarsening"]["spacing_t"][::3],
             t["coarsening"]["spacing_grows"], t["coarsening"]["N_decreases"]))
    print("   reversible echo fidelity (gamma=0): %.4f  (arrow not in the law)"
          % t["echo_fidelity"])
    passed, checks = evaluate(result, quick=quick)
    print("------------------------------- AUDIT --------------------------------")
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS (measured pieces): %s | co-emergence reading: interpretive"
          % ("GREEN" if passed else "RED"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="e008 co-emergence (2D)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    result = simulate(quick=args.quick)
    _print_report(result, quick=args.quick)
    if not args.no_write and not args.quick:
        out = os.path.join(os.path.dirname(__file__), "result.json")
        with open(out, "w") as f:
            json.dump(result, f, indent=2)
        print("\nwrote %s" % out)
    passed, _ = evaluate(result, quick=args.quick)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
