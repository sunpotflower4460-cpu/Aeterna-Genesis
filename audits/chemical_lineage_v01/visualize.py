"""Figures for the chemical lineage audit (v0.1). Results are shown, never used as an input (依頼: visualisation only).
Every panel states the protocol, the controls and the units. Nothing is drawn to suggest inheritance that the numbers do not show.
"""
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SUB = "fixed protocol, abstract closed network, no genetic code coded"


def make_all(summ, rows, inv, outdir):
    os.makedirs(outdir, exist_ok=True)
    taus = sorted({r["tau"] for r in summ})
    fmain = 0.10
    # Fig 1: parent-specific dispersion vs passive expectation
    fig, axs = plt.subplots(1, len(taus), figsize=(4.2 * len(taus), 3.8), squeeze=False)
    for ax, tau in zip(axs[0], taus):
        S = [r for r in summ if r["tau"] == tau and r["f"] == fmain]
        g = np.array([r["gen"] for r in S])
        m = np.array([r["disp_L1_mean"] for r in S])
        lo = np.array([r["disp_L1_lo"] for r in S])
        hi = np.array([r["disp_L1_hi"] for r in S])
        ax.fill_between(g, np.maximum(lo, 1e-12), np.maximum(hi, 1e-12), alpha=0.25, label="L1 95% CI")
        ax.plot(g, np.maximum(m, 1e-12), color="#0072B2", lw=2, label="L1 parent-specific dispersion")
        d0 = m[0]
        ax.plot(g, np.maximum(d0 * fmain ** g, 1e-12), "--", color="#444444", label="passive dilution f^g x dispersion(0)")
        ax.set_yscale("log")
        ax.set_title(f"tau = {tau} (f = {fmain})", fontsize=9)
        ax.set_xlabel("generation")
        ax.set_ylabel("distance to mean state (units of T)")
        ax.legend(fontsize=6)
    fig.suptitle("Parent-specific memory vs passive dilution\n" + SUB, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "parent_specific_dispersion.png"), dpi=120)
    plt.close(fig)

    # Fig 2: transfer-induced offset relative to units-only counterfactual, with shared-attractor check
    fig, axs = plt.subplots(1, len(taus), figsize=(4.2 * len(taus), 3.8), squeeze=False)
    for ax, tau in zip(axs[0], taus):
        S = [r for r in summ if r["tau"] == tau and r["f"] == fmain]
        g = np.array([r["gen"] for r in S])
        m = np.array([r["offset_L1_LR_mean"] for r in S])
        lo = np.array([r["offset_L1_LR_lo"] for r in S])
        hi = np.array([r["offset_L1_LR_hi"] for r in S])
        ax.fill_between(g, lo, hi, alpha=0.25, color="#D55E00")
        ax.plot(g, m, color="#D55E00", lw=2, label="L1 vs units-only LR")
        ax.set_title(f"tau = {tau} (f = {fmain})", fontsize=9)
        ax.set_xlabel("generation")
        ax.set_ylabel("offset (units of T)")
        ax.legend(fontsize=7)
    fig.suptitle("Transfer-induced offset from the units-only counterfactual\n" + SUB, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "transfer_offset.png"), dpi=120)
    plt.close(fig)

    # Fig 3: audit - element totals and free-energy monotonicity
    keys = list(inv.keys())
    labels = [k.replace("tau=", "tau ").replace(",f=", ", f ") for k in keys]
    res = [inv[k]["max_element_residual_end_states"] for k in keys]
    fe = [inv[k]["free_energy_max_increase_in_closed_phase"] for k in keys]
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.6))
    axs[0].bar(range(len(keys)), np.maximum(res, 1e-18), color="#009E73")
    axs[0].set_yscale("log")
    axs[0].set_xticks(range(len(keys)))
    axs[0].set_xticklabels(labels, rotation=20, fontsize=6)
    axs[0].set_title("Building-unit residual |element - T| (log)", fontsize=9)
    axs[1].bar(range(len(keys)), fe, color="#CC79A7")
    axs[1].axhline(0.0, color="#444444", lw=0.8)
    axs[1].set_xticks(range(len(keys)))
    axs[1].set_xticklabels(labels, rotation=20, fontsize=6)
    axs[1].set_title("Max free-energy increase in a closed phase (<= 0 expected)", fontsize=9)
    fig.suptitle("Conservation and free-energy audit\n" + SUB, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "audit_conservation_and_free_energy.png"), dpi=120)
    plt.close(fig)
