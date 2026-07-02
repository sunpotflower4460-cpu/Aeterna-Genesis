#!/usr/bin/env python3
"""e017 Stage 2 -- walled Rayleigh-Benard DNS: Nu(Ra) and interior delivery.

Stage 1 gave the linear ONSET (a threshold). Here we integrate the full nonlinear
walled Boussinesq (2D vorticity-streamfunction, NO-SLIP walls via Thom's wall
vorticity, periodic in x) and MEASURE what the saturated convection does:

  * the Nusselt number Nu = 1 + <w T>  (heat transported by the flow relative to
    conduction): Nu ~ 1 BELOW onset (conduction), Nu > 1 and RISING with Ra above
    onset -- convection carries heat.
  * interior DELIVERY of a consumable scalar c supplied at the BOTTOM wall and
    consumed in the bulk: by conduction alone c decays in a boundary layer and the
    upper interior is STARVED; convection CARRIES c up, so the interior is fed --
    the walled, self-consistent version of e013's "circulation feeds the interior".

The wall vorticity BC (Thom: omega_wall = -2 psi_near/dz^2) is the walled analogue
of the linear-stability wall condition; the Poisson solve (D^2 - kx^2) psi = -omega
with psi=0 at the walls is done per x-mode (batched tridiagonal).

Put in: the Boussinesq equations + no-slip walls + a bottom scalar source with bulk
consumption. NOT put in: Nu, the onset, or the interior delivery -- all measured.

Floors: a coarse 2D DNS (small Nx x Nz), mildly supercritical Ra (not turbulent);
"delivery/feeding" is the same advective transport as e013; fixed grid.

MODULE:   e017_walled_convection (Stage 2: walled DNS + Nu + delivery)
QUESTION: Does the saturated walled convection give Nu>1 above onset and deliver a consumable scalar to the starved interior?
PUT IN:   nonlinear walled Boussinesq (no-slip) + bottom scalar source with bulk consumption. Nu / onset / delivery not put in.
EMERGED:  (measured) Nu~1 below onset, Nu>1 rising above; conduction starves the interior, convection delivers the scalar there.
CLAIM TIER: measured(Nu(Ra) above 1, interior delivery by convection) ; analogy(feeding/circulation).
KNOWN MATCH: Rayleigh-Benard heat transport Nu(Ra); advective scalar transport (e013).
STATUS:   GREEN (Nu>1 above onset + interior delivery measured; coarse mildly-supercritical DNS is the floor).
A_OR_B:   (A) faithful. Hand input = Boussinesq + walls + a scalar source; the flow, Nu, and delivery are emergent.
"""

import argparse
import json
import os
import sys

import numpy as np
from numpy.fft import rfft, irfft

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

DEFAULT = {"Nx": 32, "Nz": 41, "Pr": 1.0, "Lx": 2.0, "dt": 8e-5, "steps": 12000,
           "kc": 30.0, "seed": 1, "Ra_list": [1000.0, 2500.0, 5000.0]}
QUICK = {"Nx": 24, "Nz": 33, "steps": 6000, "Ra_list": [1000.0, 5000.0]}


def dns(p, Ra):
    Nx, Nz, Lx = p["Nx"], p["Nz"], p["Lx"]
    dz = 1.0 / (Nz - 1)
    z = np.linspace(0, 1, Nz)
    kx = 2 * np.pi * np.fft.rfftfreq(Nx, d=Lx / Nx)
    M = len(kx)
    lo = np.full((M, Nz), 1 / dz ** 2)
    up = np.full((M, Nz), 1 / dz ** 2)
    dia = (-2 / dz ** 2) - kx[:, None] ** 2 * np.ones((M, Nz))
    dia[:, 0] = 1; up[:, 0] = 0; dia[:, -1] = 1; lo[:, -1] = 0

    def solve_psi(om):
        rhs = -rfft(om, axis=0); rhs[:, 0] = 0; rhs[:, -1] = 0
        b = dia.astype(complex).copy(); d = rhs.copy()
        for i in range(1, Nz):
            w = lo[:, i] / b[:, i - 1]; b[:, i] -= w * up[:, i - 1]; d[:, i] -= w * d[:, i - 1]
        x = np.zeros((M, Nz), complex); x[:, -1] = d[:, -1] / b[:, -1]
        for i in range(Nz - 2, -1, -1):
            x[:, i] = (d[:, i] - up[:, i] * x[:, i + 1]) / b[:, i]
        return irfft(x, n=Nx, axis=0)

    def ddx(f):
        return irfft(1j * kx[:, None] * rfft(f, axis=0), n=Nx, axis=0)

    def d2x(f):
        return irfft(-(kx[:, None] ** 2) * rfft(f, axis=0), n=Nx, axis=0)

    def ddz(f):
        g = np.zeros_like(f); g[:, 1:-1] = (f[:, 2:] - f[:, :-2]) / (2 * dz)
        g[:, 0] = (-3 * f[:, 0] + 4 * f[:, 1] - f[:, 2]) / (2 * dz)
        g[:, -1] = (3 * f[:, -1] - 4 * f[:, -2] + f[:, -3]) / (2 * dz)
        return g

    def d2z(f):
        g = np.zeros_like(f); g[:, 1:-1] = (f[:, 2:] - 2 * f[:, 1:-1] + f[:, :-2]) / dz ** 2
        return g

    rng = np.random.default_rng(p["seed"])
    theta = 0.01 * rng.standard_normal((Nx, Nz)); theta[:, 0] = 0; theta[:, -1] = 0
    omega = np.zeros((Nx, Nz))
    c = np.zeros((Nx, Nz))                       # consumable scalar, bottom source
    dt, Pr, kc = p["dt"], p["Pr"], p["kc"]
    for _ in range(p["steps"]):
        psi = solve_psi(omega)
        u = ddz(psi); w = -ddx(psi)
        omega[:, 0] = -2 * psi[:, 1] / dz ** 2; omega[:, -1] = -2 * psi[:, -2] / dz ** 2
        Ttot = (1 - z)[None, :] + theta
        adv_o = u * ddx(omega) + w * ddz(omega)
        omega[:, 1:-1] += dt * (-adv_o[:, 1:-1] + Pr * (d2x(omega) + d2z(omega))[:, 1:-1]
                                + Ra * Pr * ddx(Ttot)[:, 1:-1])
        adv_t = u * ddx(theta) + w * ddz(Ttot)
        theta[:, 1:-1] += dt * (-adv_t[:, 1:-1] + (d2x(theta) + d2z(theta))[:, 1:-1])
        theta[:, 0] = 0; theta[:, -1] = 0
        adv_c = u * ddx(c) + w * ddz(c)
        c[:, 1:-1] += dt * (-adv_c[:, 1:-1] + (d2x(c) + d2z(c))[:, 1:-1] - kc * c[:, 1:-1])
        c[:, 0] = 1.0; c[:, -1] = 0.0
        if not np.isfinite(omega).all():
            return {"Ra": Ra, "KE": float("nan"), "Nu": float("nan"), "c_interior": float("nan")}
    Ttot = (1 - z)[None, :] + theta
    ke = float(0.5 * np.mean(u ** 2 + w ** 2))
    Nu = 1.0 + float(np.mean(w * Ttot))          # nondim conductive flux = kappa*dT/H = 1
    upper = (z >= 0.6) & (z <= 0.9)              # interior far from the bottom source
    c_interior = float(c[:, upper].mean())
    return {"Ra": Ra, "KE": round(ke, 3), "Nu": round(Nu, 3), "c_interior": round(c_interior, 4)}


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    rows = [dns(p, Ra) for Ra in p["Ra_list"]]
    sub, sup = rows[0], rows[-1]
    return {"params": p, "rows": rows,
            "Nu_rises_with_Ra": bool(all(rows[i]["Nu"] <= rows[i + 1]["Nu"] + 1e-6
                                         for i in range(len(rows) - 1)) and sup["Nu"] > 1.1),
            "convection_above_onset": bool(sup["KE"] > 1.0 and sub["KE"] < 0.1),
            "interior_delivered_by_convection": bool(sup["c_interior"] > 3 * (sub["c_interior"] + 1e-9)
                                                     and sup["c_interior"] > 0.05),
            "Nu_range": [rows[0]["Nu"], rows[-1]["Nu"]],
            "c_interior_range": [sub["c_interior"], sup["c_interior"]]}


def evaluate(result, quick=False):
    checks = {
        "convection above onset (KE jumps)": result["convection_above_onset"],
        "Nu>1 and rises with Ra": result["Nu_rises_with_Ra"],
        "interior delivered by convection (not conduction)": result["interior_delivered_by_convection"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e017 walled RB DNS (Nu + interior delivery)", "tier": "measured",
        "put_in": "nonlinear walled Boussinesq (no-slip) + bottom scalar source with bulk consumption; Nu/onset/delivery not put in",
        "emerged": ["Nu ~ 1 below onset, Nu>1 rising with Ra: %s" % result["Nu_range"],
                    "conduction starves the interior; convection delivers the scalar there: c_interior %s"
                    % result["c_interior_range"]],
        "surprises": ["the walled saturated convection both transports heat (Nu>1) and feeds the starved interior -- e013's feeding in a real walled cell"],
        "persistence": "saturated convection above onset; sub-critical conduction starves the interior",
        "measured_numbers": {"rows": result["rows"]},
        "not_scripted_check": "Nu and c_interior are read from the saturated flow; only the equations + a source are put in",
        "claim_tier": "measured (Nu(Ra)>1, interior delivery by convection) ; analogy (feeding/circulation)",
        "floors": ["coarse 2D DNS (small grid), mildly supercritical Ra (not turbulent); fixed grid",
                   "'delivery/feeding' is the same advective transport as e013; 'heart/circulation' is analogy"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e017 walled RB DNS (Nu + delivery)")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e017 walled RB DNS: Nu(Ra) and interior delivery ===")
    for row in r["rows"]:
        tag = "CONVECTING" if row["KE"] > 1.0 else "conduction"
        print("  Ra=%7.1f: KE=%9.3f [%s]  Nu=%.3f  c_interior=%.4f"
              % (row["Ra"], row["KE"], tag, row["Nu"], row["c_interior"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (Nu>1 above onset + interior delivery measured; coarse DNS is the floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "rb_dns.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/rb_dns.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
