"""Validation figures for the P10 transport audit (v0.1).

These plots SHOW results. They are never an input to any computation (依頼 §9, AGENTS.md).
The interface is a fixed, hand-placed planar tanh profile; the figures say so in their titles.
"""
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import model  # noqa: E402
import metrics as M  # noqa: E402

NOTE = "fixed hand-placed planar interface (validation only; no emergence claim)"
C_B = "#0072B2"   # blue
C_A = "#D55E00"   # vermillion
C_G = "#009E73"   # green
C_K = "#444444"


def _phi_shade(ax, x, phi):
    ax.fill_between(x, -0.02, 1.0, where=phi > 0, color="#dddddd", alpha=0.5, lw=0, label="inside (phi>0)")
    ax.set_ylim(bottom=0.0)


def make_all(d2, d3, d4, d6, d8, exp8, outdir):
    os.makedirs(outdir, exist_ok=True)

    # ---- 1. concentration profiles
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    x = d3[128]["x"]
    phi = d3[128]["phi"]
    c_fin = d3[128]["C_final"]
    ceq = M.discrete_equilibrium(phi, 0.5, 1.0, d3[128]["dx"])
    cc = M.continuum_equilibrium(x, lambda z: model.phi_profile(z), 0.5, 1.0)
    ax = axs[0]
    _phi_shade(ax, x, phi)
    ax.plot(x, c_fin, color=C_B, lw=2.2, label="B flux, t = 40 (N=128)")
    ax.plot(x, ceq, "--", color=C_K, lw=1.2, label="discrete Boltzmann state")
    ax.plot(x, cc, ":", color=C_G, lw=1.6, label="continuum c ∝ exp(−βφ)")
    ax.set_xlabel("x (domain length = 1)")
    ax.set_ylabel("concentration c (mass = 1)")
    ax.set_title("A. Equilibrium partition (β = +0.5)\n" + NOTE, fontsize=9)
    ax.legend(fontsize=7, loc="upper right")
    ax = axs[1]
    _phi_shade(ax, x, phi)
    ax.plot(x, 1.0 + 0.5 * np.cos(2 * np.pi * x), color=C_K, lw=1.0, ls="--", label="initial c0")
    ax.plot(x, d2["A_final"], color=C_A, lw=2.0, label="A: literal F0 flux (no χ), t = 40")
    ax.plot(x, d2["B_final"], color=C_B, lw=2.0, label="B: μ-gradient flux (with χ), t = 40")
    ax.set_xlabel("x")
    ax.set_title("B. Same start, same interface: literal F0 flux vs μ flux\n" + NOTE, fontsize=9)
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "concentration_profiles.png"), dpi=120)
    plt.close(fig)

    # ---- 2. partition comparison
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    labels = ["A: F0-literal\nflux (β=+0.5)", "B: μ flux\n(β=+0.5)", "B: μ flux\n(β=−0.5)",
              "B: sharp\n(w=0.02, β=1.5)"]
    measured = [d2["A_ratio"], d2["B_ratio"], d4["rB"], d3["sharp"]["ratio_meas"]]
    predicted = [1.0, d2["B_pred"], d4["pB"], d3["sharp"]["ratio_disc"]]
    xi = np.arange(len(labels))
    ax.bar(xi - 0.18, measured, 0.36, color=[C_A, C_B, C_B, C_B], label="measured (t_eq)")
    ax.bar(xi + 0.18, predicted, 0.36, color="white", edgecolor=C_K, hatch="//", label="predicted (discrete Boltzmann)")
    ax.axhline(1.0, color=C_K, lw=0.8, ls=":")
    ax.set_xticks(xi)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("inside / outside concentration ratio")
    ax.set_title("Partition: the χ-free literal flux gives 1 (no partition); the μ flux gives the Boltzmann ratio\n" + NOTE,
                 fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "partition_comparison.png"), dpi=120)
    plt.close(fig)

    # ---- 3. free-energy trace
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axs[0]
    for N, col in ((64, C_G), (128, C_B), (256, C_K)):
        R = d8[(0.5, N)]
        ax.plot(R["t"], R["F"] - R["F"][0], color=col, lw=1.6, label=f"N={N}, β=+0.5 (μ flux)")
    R = d8[(-0.5, 128)]
    ax.plot(R["t"], R["F"] - R["F"][0], color=C_A, lw=1.2, ls="--", label="N=128, β=−0.5 (μ flux)")
    ax.axhline(0.0, color=C_K, lw=0.6)
    ax.set_xlabel("t")
    ax.set_ylabel("F_ref(t) − F_ref(0)")
    ax.set_title("Free energy decreases (μ flux, fixed interface)\n" + NOTE, fontsize=9)
    ax.legend(fontsize=7)
    ax = axs[1]
    R = d8[(0.5, 128)]
    t = R["t"]
    dF = np.gradient(R["F"], t)
    diss = np.array([model.dissipation_mu(c, R["phi"], 0.5, R["D"], R["dx"]) for c in R["C"]])
    ax.plot(t, dF, color=C_B, lw=1.6, label="numerical dF/dt")
    ax.plot(t, -diss, color=C_K, lw=1.0, ls="--", label="−dissipation (identity E-1)")
    ax.set_xlabel("t")
    ax.set_ylabel("dF/dt")
    ax.set_yscale("symlog", linthresh=1e-6)
    ax.set_title("Energy identity (N=128, β=+0.5)\n" + NOTE, fontsize=9)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "free_energy_trace.png"), dpi=120)
    plt.close(fig)
