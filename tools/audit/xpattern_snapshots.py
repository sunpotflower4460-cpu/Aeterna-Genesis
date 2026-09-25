"""Before/after pictures of X-pattern events, re-run from t=0 (for the P2 audit report).

Re-runs the unchanged open_ended probe loop for a pattern's recorded start condition with the audit's
fresh seeds, keeps the field at every snapshot, and for the first occurrence of the pattern writes

    audit/png/<pattern>_amp.png    |psi| before | after  (viridis)
    audit/png/<pattern>_phase.png  arg(psi) before | after (diverging)

plus a one-line caption with the measured scalars. Visualisation only; it measures nothing new.

    python tools/audit/xpattern_snapshots.py X-72162ca538 X-6ceabe0fd8
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

from ai_lab import lab  # noqa: E402
from ai_lab.dream import open_ended as oe  # noqa: E402
from genesis.models import ginzburg_landau as gl  # noqa: E402
from tools.audit.xpattern_audit import _seed  # noqa: E402
from tools.snapshot import colormap, write_png  # noqa: E402

_OUT = _REPO / "audit" / "png"


def run_with_fields(rec: dict) -> tuple[list[dict], list[np.ndarray]]:
    """open_ended._probe, but also returning psi at each snapshot (same schedule, same numerics)."""
    edge, macro_steps, nsnap = lab.STEPS_2D[True]
    shape = (edge, edge)
    knobs = dict(rec["knobs"])
    p = lab._apply_knobs(dict(gl.DEFAULTS), knobs)
    base_dt = float(p["dt"])
    nsub = lab._cfl_substeps(float(p["Du"]), base_dt, ndim=2)
    p["dt"] = base_dt / nsub
    total = macro_steps * nsub
    rng = np.random.default_rng(int(rec["seed"]))
    psi = lab.make_ic(str(rec["family"]), shape, float(p["noise_amplitude"]), rng,
                      corr_len=float(knobs.get("correlation_length", 1.0)))
    snap_every = max(1, total // max(16, nsnap * 3))
    snaps, fields = [], []
    for t in range(total):
        psi = gl.step(psi, t * p["dt"], p)
        if t % snap_every != 0 and t != total - 1:
            continue
        snaps.append(oe._snapshot_features(psi, physical_time=(t + 1) * p["dt"], shape=shape))
        fields.append(psi.copy())
    return snaps, fields


def _pair(a: np.ndarray, b: np.ndarray, *, diverging: bool, lo: float, hi: float, px: int = 6) -> np.ndarray:
    def tile(x):
        n = np.clip((x - lo) / (hi - lo + 1e-12), 0, 1)
        return colormap(np.kron(n, np.ones((px, px))), diverging=diverging)
    gap = np.full((a.shape[0] * px, 8, 3), 255, np.uint8)
    return np.concatenate([tile(a), gap, tile(b)], axis=1)


def main(pids: list[str]) -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    unknown = json.loads((_REPO / "ai_lab/discoveries/unknown_followups.json").read_text())["patterns"]
    for pid in pids:
        focus = unknown[pid]["search_focus"]
        for i in range(40):
            rec = {"family": focus["family"], "knobs": focus["knobs"], "seed": _seed(pid, i), "quick": True}
            snaps, fields = run_with_fields(rec)
            # analysis_start_time exactly as open_ended._probe computes it
            _, macro_steps, _ = lab.STEPS_2D[True]
            base_t = macro_steps * float(lab._apply_knobs(dict(gl.DEFAULTS), dict(focus["knobs"]))["dt"])
            start = min(base_t * 0.8, max(float(focus["knobs"].get("quench_duration", 0.0)), base_t * 0.2))
            probe = {"snapshots": snaps, "analysis_start_time": start}
            hits = [e for e in oe.detect_episodes(probe, max_episodes=5) if e["pattern_id"] == pid]
            if not hits:
                continue
            ep = hits[0]
            j = next(k for k in range(len(snaps) - 1) if abs(snaps[k + 1]["physical_time"] - ep["physical_time"]) < 1e-9)
            a0, a1 = np.abs(fields[j]), np.abs(fields[j + 1])
            hi = float(max(a0.max(), a1.max()))
            write_png(_pair(a0, a1, diverging=False, lo=0.0, hi=hi), _OUT / f"{pid}_amp.png")
            write_png(_pair(np.angle(fields[j]), np.angle(fields[j + 1]), diverging=True, lo=-np.pi, hi=np.pi),
                      _OUT / f"{pid}_phase.png")
            s0, s1 = snaps[j], snaps[j + 1]
            print(json.dumps({"pattern": pid, "seed": rec["seed"], "t": [s0["physical_time"], s1["physical_time"]],
                              "mean_amp": [round(s0["mean_amp"], 4), round(s1["mean_amp"], 4)],
                              "defects": [s0["defect_count"], s1["defect_count"]],
                              "net_charge": [s0["net_topological_charge"], s1["net_topological_charge"]]}))
            break
        else:
            print(json.dumps({"pattern": pid, "reproduced": False, "seeds_tried": 40}))


if __name__ == "__main__":
    main(sys.argv[1:])
