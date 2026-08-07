"""Stricter geometry hypothesis lane for Adaptive Dream.

The first production probe showed why a naive triangle detector is dangerous: with many vortices,
some arbitrary three points often look triangular.  This module therefore requires an isolated
mutual-nearest triad to persist across consecutive snapshots, and compares its later split rate
against persistent NON-triangular triads before increasing belief in the triangle hypothesis.
"""
from __future__ import annotations

import json
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from ai_lab import lab
from genesis.diagnostics import geometry_events as geom
from genesis.models import ginzburg_landau as gl

_REPO = Path(__file__).resolve().parents[2]
_HYPOTHESES = _REPO / "ai_lab" / "discoveries" / "hypothesis_ledger.json"
_EASY = _REPO / "ai_lab" / "reports" / "easy"


def _persistent_anchor(snapshots: list[dict[str, Any]], *, kind: str, shape: tuple[int, int]) -> tuple[int, dict[str, Any]] | None:
    """Find the first same local triad observed in two consecutive snapshots."""
    key = "triangle" if kind == "triangle" else "control"
    for i in range(1, len(snapshots)):
        a = snapshots[i - 1].get(key)
        b = snapshots[i].get(key)
        if a and b and geom.same_local_triad(a, b, shape):
            return i - 1, {**a, "step": snapshots[i - 1]["step"], "persistence_snapshots": 2}
    return None


def _split_after(snapshots: list[dict[str, Any]], anchor_index: int, anchor: dict[str, Any], shape: tuple[int, int]) -> bool:
    max_side = max(float(x) for x in anchor["side_lengths"])
    neighbourhood = max(4.0, 1.8 * max_side)
    link = max(2.0, 1.05 * max_side)
    streak = 0
    for snap in snapshots[anchor_index + 2:]:
        local = geom.local_cluster_count(
            snap["points"], centre=anchor["centroid"], shape=shape,
            neighbourhood_radius=neighbourhood, link_radius=link,
        )
        if local["local_vortices"] >= 2 and local["clusters"] >= 2:
            streak += 1
            if streak >= 2:
                return True
        else:
            streak = 0
    return False


def _geometry_probe(rec: dict[str, Any]) -> dict[str, Any]:
    quick = bool(rec.get("quick", True))
    edge, steps, nsnap = lab.STEPS_2D[quick]
    shape = (edge, edge)
    p = lab._apply_knobs(dict(gl.DEFAULTS), rec["knobs"])
    base_dt = float(p["dt"])
    nsub = lab._cfl_substeps(float(p["Du"]), base_dt, ndim=2)
    p["dt"] = base_dt / nsub
    total = steps * nsub
    rng = np.random.default_rng(int(rec["seed"]))
    psi = lab.make_ic(
        rec["family"], shape, float(p["noise_amplitude"]), rng,
        corr_len=float(rec["knobs"].get("correlation_length", 1.0)),
    )
    snap_every = max(1, total // max(10, nsnap * 2))
    snapshots: list[dict[str, Any]] = []
    for t in range(total):
        psi = gl.step(psi, t * p["dt"], p)
        if not np.all(np.isfinite(psi)):
            break
        if t % snap_every != 0 and t != total - 1:
            continue
        points = geom.vortex_points_2d(psi)
        snapshots.append({
            "step": t,
            "points": points,
            "triangle": geom.best_triangle(points, shape),
            "control": geom.best_control_triad(points, shape),
        })

    # A run is a triangle case if a persistent triangle exists. Only runs without one may become
    # non-triangle controls; this prevents the same run from being counted on both sides.
    tri_found = _persistent_anchor(snapshots, kind="triangle", shape=shape)
    ctrl_found = None if tri_found else _persistent_anchor(snapshots, kind="control", shape=shape)
    category = "triangle" if tri_found else ("control" if ctrl_found else None)
    found = tri_found or ctrl_found
    anchor_index, anchor = found if found else (None, None)
    split = bool(found and _split_after(snapshots, int(anchor_index), anchor, shape))

    compact_series = [{
        "step": s["step"], "vortices": len(s["points"]),
        "triangle": bool(s["triangle"]), "control": bool(s["control"]),
    } for s in snapshots]
    return {
        "trial_index": rec.get("trial_index"),
        "family": rec["family"], "knobs": rec["knobs"], "seed": rec["seed"],
        "triad_type": category,
        "triangle_seen": category == "triangle",
        "control_seen": category == "control",
        "triangle": anchor if category == "triangle" else None,
        "control": anchor if category == "control" else None,
        "fission_like_after_triangle": bool(category == "triangle" and split),
        "fission_like_after_control": bool(category == "control" and split),
        "series": compact_series,
        "honesty": {
            "triangle_was_seeded": False,
            "persistent_two_snapshots_required": True,
            "mutual_nearest_triad_required": True,
            "matched_nontriangle_control": True,
            "fission_like_is_biological_cell_division": False,
            "changes_level_gate": False,
        },
    }


def run_geometry_probes(
    results: list[dict[str, Any]], *, top: int = 12, broad: int = 12,
    workers: int = 4, quick: bool = True, seed: int = 0,
) -> list[dict[str, Any]]:
    stable = [r for r in results if r.get("score") is not None]
    chosen = stable[:max(0, top)]
    rest = stable[max(0, top):]
    rng = random.Random(seed ^ 0xC071)
    if rest and broad > 0:
        ids = list(range(len(rest)))
        rng.shuffle(ids)
        chosen += [rest[i] for i in ids[:min(broad, len(ids))]]
    payload = [{**r, "quick": bool(quick)} for r in chosen]
    if workers <= 1:
        return [_geometry_probe(x) for x in payload]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_geometry_probe, payload))


def geometry_summary(probes: list[dict[str, Any]]) -> dict[str, Any]:
    triangles = [p for p in probes if p.get("triangle_seen")]
    controls = [p for p in probes if p.get("control_seen")]
    tri_splits = [p for p in triangles if p.get("fission_like_after_triangle")]
    ctrl_splits = [p for p in controls if p.get("fission_like_after_control")]
    tri_rate = len(tri_splits) / len(triangles) if triangles else None
    ctrl_rate = len(ctrl_splits) / len(controls) if controls else None
    excess = None if tri_rate is None or ctrl_rate is None else tri_rate - ctrl_rate
    return {
        "detector_version": 2,
        "probed": len(probes),
        "triangle_seen": len(triangles),
        "fission_like_after_triangle": len(tri_splits),
        "triangle_without_fission": len(triangles) - len(tri_splits),
        "control_seen": len(controls),
        "fission_like_after_control": len(ctrl_splits),
        "control_without_fission": len(controls) - len(ctrl_splits),
        "rate_given_triangle": None if tri_rate is None else round(tri_rate, 4),
        "rate_given_control": None if ctrl_rate is None else round(ctrl_rate, 4),
        "triangle_excess_rate": None if excess is None else round(excess, 4),
        "comparison_ready": bool(len(triangles) >= 3 and len(controls) >= 3),
        "note": "Only persistent mutual-nearest triads count. A fission-like event is geometry, not biological cell division.",
    }


def update_triangle_hypothesis(doc: dict[str, Any], *, burst_id: str, summary: dict[str, Any]) -> dict[str, Any]:
    hypotheses = doc.setdefault("hypotheses", [])
    h = next((x for x in hypotheses if x.get("id") == "three-vortex-triangle-fission"), None)
    if h is None:
        h = {
            "id": "three-vortex-triangle-fission",
            "statement": "A persistent isolated three-vortex triangle may be followed by local splitting more often than a non-triangular three-vortex arrangement.",
            "counter_statement": "Triangle shape is incidental; its later split rate is not higher than matched non-triangle triads.",
            "falsification_condition": "Across repeated bursts, triangle split rate fails to exceed the matched-control split rate.",
            "status": "TESTING", "support": 0, "contradiction": 0,
            "support_cycles": [], "confidence": 0.5, "comparison_bursts": 0,
        }
        hypotheses.append(h)

    # Do NOT count each split as support. One burst contributes at most one evidence unit, and only
    # when both triangle and control samples are present. This prevents dense-vortex hours from
    # overpowering the hypothesis ledger through sample-count inflation.
    if summary.get("comparison_ready"):
        h["comparison_bursts"] = int(h.get("comparison_bursts", 0)) + 1
        excess = float(summary.get("triangle_excess_rate") or 0.0)
        if excess >= 0.10:
            h["support"] = int(h.get("support", 0)) + 1
            cycles = set(h.get("support_cycles") or [])
            cycles.add(burst_id)
            h["support_cycles"] = sorted(cycles)
        elif excess <= 0.02:
            h["contradiction"] = int(h.get("contradiction", 0)) + 1

    s, c = int(h.get("support", 0)), int(h.get("contradiction", 0))
    cycles = h.get("support_cycles") or []
    cap = 0.65 if len(cycles) < 2 else 0.85
    # With no comparison burst, keep the prior confidence: insufficient controls are ignorance,
    # not support and not contradiction.
    if int(h.get("comparison_bursts", 0)) > 0:
        h["confidence"] = round(min(cap, max(0.15, (s + 1) / (s + c + 2))), 4)
    if s >= 2 and c >= 2:
        h["status"] = "UNCERTAIN"
    elif s >= 2:
        h["status"] = "SUPPORTED"
    elif c >= 2 and s == 0:
        h["status"] = "WEAKENED"
    else:
        h["status"] = "TESTING"
    h["last_burst"] = burst_id
    h["last_comparison"] = {
        k: summary.get(k) for k in (
            "triangle_seen", "fission_like_after_triangle", "control_seen",
            "fission_like_after_control", "rate_given_triangle", "rate_given_control",
            "triangle_excess_rate", "comparison_ready",
        )
    }
    _HYPOTHESES.parent.mkdir(parents=True, exist_ok=True)
    _HYPOTHESES.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    return doc


def write_easy_report(
    report: dict[str, Any], *, geometry: dict[str, Any], director_refreshed: bool, stamp: str,
) -> dict[str, str]:
    c = report.get("counts") or {}
    native = ((report.get("adaptive_research") or {}).get("native_3d") or {})
    reproduced = int(c.get("reproduced", 0))
    dimension_hits = int(native.get("dimension_emergence", 0))
    new_regions = int(((report.get("adaptive_research") or {}).get("coverage_progress") or {}).get("new_regions", 0))
    tn = int(geometry.get("triangle_seen", 0)); ts = int(geometry.get("fission_like_after_triangle", 0))
    cn = int(geometry.get("control_seen", 0)); cs = int(geometry.get("fission_like_after_control", 0))

    if geometry.get("comparison_ready"):
        tr = round(100 * float(geometry.get("rate_given_triangle") or 0.0))
        cr = round(100 * float(geometry.get("rate_given_control") or 0.0))
        if tr > cr:
            one_line = f"三角に並んだ3つ組は {tr}%、三角ではない3つ組は {cr}% で、その後に分かれるような変化が見えました。まだ回数を増やして確かめます。"
        else:
            one_line = f"今のところ、三角の3つ組だけが特別に分かれやすいとは言えません（三角 {tr}%、比較 {cr}%）。"
    elif tn:
        one_line = f"厳しい条件で『三角に並んだ3つの渦』を {tn} 件見つけました。比較相手がまだ足りないので結論は保留です。"
    else:
        one_line = "今回は『3つの渦の三角形』について、結論を出せるだけの例は集まりませんでした。"

    easy = {
        "version": 2, "burst_id": report.get("burst_id"), "generated_at": report.get("generated_at"),
        "one_line": one_line,
        "what_we_did": f"平面の世界で {int(c.get('mass_2d_trials', 0)):,} 通り、立体の世界で {int(c.get('native_3d_trials', 0)):,} 通りを試しました。",
        "what_we_found": f"やり直しても似た結果になった候補は {reproduced} 件。立体から始めた方が強かった候補は {dimension_hits} 件。新しく調べた範囲は {new_regions} 区画です。",
        "triangle_question": (
            f"今回は、3つが互いに近い仲間としてまとまり、その並びが続いた場合だけ数えました。"
            f" 三角の3つ組は {tn} 件（その後に分かれたように見えたのは {ts} 件）。"
            f" 三角ではない比較用の3つ組は {cn} 件（分かれたのは {cs} 件）でした。"
        ),
        "what_next": "結果をまとめて次の調べ方を考え直しました。" if director_refreshed else "次の大きな見直しまで同じ方針で例を増やします。",
        "important_note": "『分かれた』は細胞分裂そのものという意味ではありません。また、三角形が原因だとは、比較して差が何度も再現するまで判断しません。",
        "director_refreshed": bool(director_refreshed), "geometry_summary": geometry,
    }
    out = _EASY / stamp
    out.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out / "report.json", out / "report.md"
    json_path.write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    md = "\n".join([
        "# やさしい実験レポート", "", f"**ひとことで：** {one_line}", "",
        "## 今回なにをした？", easy["what_we_did"], "", "## なにが分かった？", easy["what_we_found"], "",
        "## 3つの渦の三角形は？", easy["triangle_question"], "", "## 次は？", easy["what_next"], "",
        f"> {easy['important_note']}", "",
    ])
    md_path.write_text(md)
    _EASY.mkdir(parents=True, exist_ok=True)
    (_EASY / "latest.json").write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    (_EASY / "latest.md").write_text(md)
    return {"json": str(json_path), "markdown": str(md_path), "latest": str(_EASY / "latest.json")}
