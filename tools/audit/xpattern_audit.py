"""P2 treasure audit, part 2: what are the "unnamed changes" X-… ?

An X pattern (ai_lab/dream/open_ended.py) is a hash of a quantized sign/magnitude vector of jumps in up to
five of eleven *global scalar* observables of a 2D TDGL quench. Its "known" labels only fire when the vortex
count crosses 0<->1, so ordinary physics (amplitude growth after the quench, pair annihilation, coarsening)
is tagged "unlabeled" by construction. This audit asks, for every pattern, which ordinary mechanism explains
it before anything is called a discovery.

Stage A (all patterns, no compute): classify each fingerprint by which observables jump and in which
direction (amplitude-only growth, defect loss/gain, spectral rearrangement, ...).

Stage B (re-run from t=0): for patterns that carry a reproducible start condition (unknown_followups
``search_focus``), re-probe fresh deterministic seeds with the unchanged ``open_ended._probe`` and label every
occurrence of the target pattern:

    H1 pair_annihilation    defect count falls by an even number, net topological charge unchanged
    H4 last_defects_vanish  defect count reaches 0 (finite-box end of coarsening)
    H2 defect_count_change  other change in defect count (odd steps: detection noise / boundary)
    H3 amplitude_ordering   no defect change; mean |psi| rises while still below 95% of its final plateau
    H3b amplitude_relaxation no defect change; amplitude already saturated (smoothing / relaxation)
    UNEXPLAINED             none of the above

and H6 (binning sensitivity): whether the pattern ID survives moving the fingerprint thresholds by +-10%.
A pattern gets the label that explains >=80% of its reproduced occurrences, otherwise MIXED;
NOT_REPRODUCED if the fresh seeds never show it. UNEXPLAINED patterns are the real treasure candidates.

Read-only on ai_lab/: it imports the detector unchanged and never rewrites historical IDs.

    python tools/audit/xpattern_audit.py --seeds 3 --workers 4
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

from ai_lab.dream import open_ended as oe  # noqa: E402

_GRAPH = _REPO / "ai_lab" / "discoveries" / "emergence_graph.json"
_UNKNOWN = _REPO / "ai_lab" / "discoveries" / "unknown_followups.json"
_MECH = _REPO / "ai_lab" / "discoveries" / "x_mechanisms.json"
_OUT = _REPO / "audit"
_AMP = {"mean_amp", "amp_std", "gradient_rms", "high_amp_fraction", "phase_coherence"}
_SPECTRAL = {"spectral_entropy", "spectral_k_rms", "spectral_anisotropy"}


# ---------------------------------------------------------------- stage A
def parse_fp(fp: str) -> dict[str, str]:
    out = {}
    for piece in (fp or "").split("|"):
        if ":" in piece:
            k, v = piece.split(":", 1)
            out[k] = v  # e.g. "+L"
    return out


def static_class(fp: str) -> str:
    f = parse_fp(fp)
    keys = set(f)
    if not keys:
        return "EMPTY"
    if "defect_count" in f:
        return "DEFECT_LOSS" if f["defect_count"].startswith("-") else "DEFECT_GAIN"
    if "net_topological_charge" in f:
        return "CHARGE_CHANGE"
    if keys <= _AMP:
        return "AMPLITUDE_GROWTH" if all(v.startswith("+") for v in f.values()) else "AMPLITUDE_MIXED"
    if keys & _SPECTRAL and not keys - _SPECTRAL - _AMP:
        return "SPECTRAL_REARRANGEMENT"
    return "OTHER"


# ---------------------------------------------------------------- stage B
def fingerprint(delta: np.ndarray, *, floor: float = 0.15, s_m: float = 0.35, m_l: float = 0.8) -> str | None:
    """open_ended._episode_fingerprint with adjustable thresholds (identical at the defaults)."""
    ranked = sorted(range(len(oe._FEATURES)), key=lambda i: abs(float(delta[i])), reverse=True)
    pieces = []
    for i in ranked:
        v = float(delta[i])
        if abs(v) < floor:
            continue
        mag = "S" if abs(v) < s_m else ("M" if abs(v) < m_l else "L")
        pieces.append(f"{oe._FEATURES[i]}:{'+' if v > 0 else '-'}{mag}")
        if len(pieces) >= 5:
            break
    return "|".join(sorted(pieces)) if pieces else None


def _pid(fp: str | None) -> str | None:
    return None if fp is None else "X-" + hashlib.sha256(fp.encode()).hexdigest()[:10]


def _seed(pid: str, i: int) -> int:
    return int(hashlib.sha256(f"p2-audit|{pid}|{i}".encode()).hexdigest()[:8], 16) % 1_000_000


def _label(before: dict, after: dict, final_amp: float) -> str:
    d0, d1 = before["defect_count"], after["defect_count"]
    q0, q1 = before["net_topological_charge"], after["net_topological_charge"]
    if d1 != d0:
        if d1 == 0 and d0 > 0:
            return "H4_last_defects_vanish"
        if d0 - d1 >= 2 and (d0 - d1) % 2 == 0 and q0 == q1:
            return "H1_pair_annihilation"
        return "H2_defect_count_change"
    if after["mean_amp"] > before["mean_amp"] and before["mean_amp"] < 0.95 * final_amp:
        return "H3_amplitude_ordering"
    if before["mean_amp"] >= 0.95 * final_amp:
        return "H3b_amplitude_relaxation"
    return "UNEXPLAINED"


def probe_pattern(job: dict) -> dict:
    pid, focus, seeds = job["pid"], job["focus"], job["seeds"]
    occurrences = []
    for i in range(seeds):
        rec = {"family": focus["family"], "knobs": focus["knobs"], "seed": _seed(pid, i), "quick": True}
        probe = oe._probe(rec)
        snaps = probe["snapshots"]
        if not probe["finite"] or len(snaps) < 4:
            continue
        matrix = np.asarray([[float(s[k]) for k in oe._FEATURES] for s in snaps])
        delta = np.diff(matrix, axis=0) / oe._robust_scales(matrix)
        final_amp = float(np.median([s["mean_amp"] for s in snaps[-3:]]))
        for ep in oe.detect_episodes(probe, max_episodes=5):
            if ep["pattern_id"] != pid:
                continue
            j = next(k for k in range(len(snaps) - 1) if abs(snaps[k + 1]["physical_time"] - ep["physical_time"]) < 1e-9)
            assert _pid(fingerprint(delta[j])) == pid, "re-implemented fingerprint must match the detector"
            variants = {_pid(fingerprint(delta[j], floor=0.15 * f, s_m=0.35 * f, m_l=0.8 * f)) for f in (0.9, 1.1)}
            occurrences.append({
                "seed": rec["seed"],
                "time": ep["physical_time"],
                "quench_duration": float(focus["knobs"].get("quench_duration", 0.0)),
                "label": _label(snaps[j], snaps[j + 1], final_amp),
                "defects": [snaps[j]["defect_count"], snaps[j + 1]["defect_count"]],
                "mean_amp": [round(snaps[j]["mean_amp"], 6), round(snaps[j + 1]["mean_amp"], 6)],
                "final_mean_amp": round(final_amp, 6),
                "id_stable_under_pm10pct_thresholds": variants == {pid},
            })
    return {"pattern_id": pid, "seeds_run": seeds, "occurrences": occurrences}


def verdict(occ: list[dict]) -> tuple[str, float]:
    if not occ:
        return "NOT_REPRODUCED", 0.0
    c = collections.Counter(o["label"] for o in occ)
    top, n = c.most_common(1)[0]
    share = n / len(occ)
    return (top if share >= 0.8 else "MIXED"), round(share, 3)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", type=int, default=3, help="fresh seeds per pattern for stage B")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="only the N most-observed patterns (0 = all)")
    a = ap.parse_args()
    _OUT.mkdir(exist_ok=True)

    graph = json.loads(_GRAPH.read_text())["patterns"]
    unknown = json.loads(_UNKNOWN.read_text())["patterns"]
    mech = json.loads(_MECH.read_text()).get("patterns", {}) if _MECH.is_file() else {}
    rows = {}
    for p in graph:
        pid = p["pattern_id"]
        rows[pid] = {
            "pattern_id": pid,
            "fingerprint": p.get("fingerprint"),
            "observations": p.get("observations"),
            "n_seeds": len(p.get("seeds") or []),
            "n_conditions": len(p.get("conditions") or []),
            "static_class": static_class(p.get("fingerprint")),
            "bot_followup_status": (unknown.get(pid) or {}).get("status"),
            "bot_mechanism_status": (mech.get(pid) or {}).get("status"),
        }

    jobs = [{"pid": pid, "focus": row["search_focus"], "seeds": a.seeds}
            for pid, row in unknown.items()
            if pid in rows and (row.get("search_focus") or {}).get("family") and isinstance(row["search_focus"].get("knobs"), dict)]
    jobs.sort(key=lambda j: -(rows[j["pid"]]["observations"] or 0))
    if a.limit:
        jobs = jobs[: a.limit]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for res in ex.map(probe_pattern, jobs):
            row = rows[res["pattern_id"]]
            row["verdict"], row["verdict_share"] = verdict(res["occurrences"])
            row["reproduced"] = len(res["occurrences"])
            row["seeds_run"] = res["seeds_run"]
            row["binning_unstable_share"] = (round(sum(not o["id_stable_under_pm10pct_thresholds"] for o in res["occurrences"])
                                                   / len(res["occurrences"]), 3) if res["occurrences"] else None)
            row["occurrences"] = res["occurrences"]
            print(f"  {res['pattern_id']} {row['static_class']:<22} {row['verdict']:<26} n={row['reproduced']}", flush=True)

    with (_OUT / "xpatterns.jsonl").open("w", encoding="utf-8") as fh:
        for row in sorted(rows.values(), key=lambda r: -(r["observations"] or 0)):
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    tested = [r for r in rows.values() if "verdict" in r]
    obs_by_static = collections.Counter()
    for r in rows.values():
        obs_by_static[r["static_class"]] += r["observations"] or 0
    summary = {
        "patterns": len(rows),
        "static_class_counts": dict(collections.Counter(r["static_class"] for r in rows.values())),
        "static_class_observations": dict(obs_by_static),
        "stage_b_tested": len(tested),
        "stage_b_seeds_per_pattern": a.seeds,
        "verdict_counts": dict(collections.Counter(r["verdict"] for r in tested)),
        "unexplained": sorted(r["pattern_id"] for r in tested if r["verdict"] in ("UNEXPLAINED", "MIXED")),
        "binning_unstable_patterns": sorted(r["pattern_id"] for r in tested if (r.get("binning_unstable_share") or 0) >= 0.5),
    }
    (_OUT / "xpatterns_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
