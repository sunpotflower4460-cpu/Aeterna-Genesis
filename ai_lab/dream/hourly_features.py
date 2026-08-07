"""Hourly discovery features for Adaptive Dream v3.

Adds three things without changing scientific truth gates:
1) full start-side 3D screening (same GL law, all five allowed knobs + honest IC families),
2) observation-only three-vortex triangle -> later cluster-split probes,
3) very plain Japanese reports intended to be readable by a middle-school student.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from ai_lab import lab
from ai_lab.dream import adaptive
from genesis.diagnostics import geometry_events as geom
from genesis.diagnostics import measures
from genesis.models import ginzburg_landau as gl

_REPO = Path(__file__).resolve().parents[2]
_HYPOTHESES = _REPO / "ai_lab" / "discoveries" / "hypothesis_ledger.json"
_EASY = _REPO / "ai_lab" / "reports" / "easy"

STEPS_3D = {True: (20, 220, 8), False: (32, 300, 10)}


def _checksum(psi: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(psi.real).tobytes())
    h.update(np.ascontiguousarray(psi.imag).tobytes())
    return h.hexdigest()[:16]


def _screen3d(tr: dict[str, Any]) -> dict[str, Any]:
    """Direct t=0 3D screen using the same expanded start-side knobs as the 2D Lab."""
    edge, steps, nsnap = STEPS_3D[bool(tr.get("quick", True))]
    shape = (edge, edge, edge)
    knobs = tr["knobs"]
    p = lab._apply_knobs(dict(gl.DEFAULTS), knobs)
    base_dt = float(p["dt"])
    nsub = lab._cfl_substeps(float(p["Du"]), base_dt, ndim=3)
    p["dt"] = base_dt / nsub
    total = steps * nsub
    rng = np.random.default_rng(int(tr["seed"]))
    psi = lab.make_ic(
        tr["family"], shape, float(p["noise_amplitude"]), rng,
        corr_len=float(knobs.get("correlation_length", 1.0)),
    )
    traj: list[dict[str, Any]] = []
    snap = max(1, total // nsnap)
    for t in range(total):
        psi = gl.step(psi, t * p["dt"], p)
        if not np.all(np.isfinite(psi)):
            return {**tr, "status": "unstable", "dimension": 3, "reached_level": None,
                    "score": None, "complexity": None, "measured_by": {}, "checksum": None,
                    "reason": "numerical_instability"}
        if t % snap == 0 or t == total - 1:
            _, prom = measures.structure_factor_peak(psi)
            traj.append({
                "mean_amp": measures.mean_amplitude(psi),
                "sk_prom": prom,
                "defects": measures.winding_defect_count(psi),
            })
    level, _, mb = measures.assess_level(traj)
    field_real = bool(np.max(np.abs(psi.imag)) == 0.0)
    raw_level = level
    note = None
    if field_real and level >= 2:
        level = 1
        note = "winding_artifact_real_field"
    complexity = lab.spectral_complexity(psi)
    out = {
        **tr,
        "status": "native_3d_screened",
        "dimension": 3,
        "reached_level": int(level),
        "reached_level_raw": int(raw_level),
        "score": lab.score_run(level, mb, complexity),
        "complexity": round(float(complexity), 4),
        "measured_by": mb,
        "checksum": _checksum(psi),
        "field_real": field_real,
    }
    if note:
        out["winding_note"] = note
    return out


def run_full_native_3d(
    *, start_index: int, n: int, workers: int, allocation: dict[str, float],
    focus: dict[str, Any] | None, master_seed: int, quick: bool,
) -> dict[str, Any]:
    """Independent 3D exploration across family + all five allowed knobs; never gated by 2D."""
    plan = adaptive.make_trial_plan(
        start_index=start_index, n=max(0, n), allocation=allocation,
        focus=focus, master_seed=master_seed ^ 0x3D3D,
    )
    payload = [{**x, "quick": bool(quick)} for x in plan]
    if workers <= 1:
        results = [_screen3d(x) for x in payload]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(_screen3d, payload, chunksize=max(1, len(payload) // (workers * 8))))
    results.sort(key=lab._score_key, reverse=True)
    return {"results": results, "n": len(results), "next_index": start_index + len(payload)}


def _paired2d(rec: dict[str, Any]) -> dict[str, Any]:
    r = lab._screen_ic(rec["family"], rec["knobs"], int(rec["seed"]), quick=True)
    level2 = None if r.get("reached_level") is None else int(r["reached_level"])
    level3 = None if rec.get("reached_level") is None else int(rec["reached_level"])
    delta = None if level2 is None or level3 is None else level3 - level2
    return {**rec, "paired_2d_level": level2, "dimension_delta": delta}


def compare_full3d_top(results: list[dict[str, Any]], *, top: int, workers: int) -> list[dict[str, Any]]:
    selected = [r for r in results if r.get("reached_level") is not None][:max(0, top)]
    if workers <= 1:
        return [_paired2d(x) for x in selected]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_paired2d, selected))


def _geometry_probe(rec: dict[str, Any]) -> dict[str, Any]:
    """Replay one 2D run and watch naturally formed vortex geometry through time."""
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
    series: list[dict[str, Any]] = []
    anchor = None
    split_streak = 0
    fission_like = False
    strongest = None
    for t in range(total):
        psi = gl.step(psi, t * p["dt"], p)
        if not np.all(np.isfinite(psi)):
            break
        if t % snap_every != 0 and t != total - 1:
            continue
        points = geom.vortex_points_2d(psi)
        triangle = geom.best_triangle(points, shape)
        if triangle and (strongest is None or triangle["triangle_score"] > strongest["triangle_score"]):
            strongest = {**triangle, "step": t, "vortex_count": len(points)}
        if anchor is None and triangle and triangle.get("qualified"):
            max_side = max(float(x) for x in triangle["side_lengths"])
            anchor = {
                **triangle,
                "step": t,
                "neighbourhood_radius": max(4.0, 1.8 * max_side),
                "link_radius": max(2.0, 1.05 * max_side),
            }
        local = None
        if anchor is not None and t >= int(anchor["step"]):
            local = geom.local_cluster_count(
                points,
                centre=anchor["centroid"],
                shape=shape,
                neighbourhood_radius=float(anchor["neighbourhood_radius"]),
                link_radius=float(anchor["link_radius"]),
            )
            if t > int(anchor["step"]) and local["local_vortices"] >= 2 and local["clusters"] >= 2:
                split_streak += 1
            else:
                split_streak = 0
            if split_streak >= 2:
                fission_like = True
        series.append({
            "step": t,
            "vortices": len(points),
            "triangle_score": None if triangle is None else triangle["triangle_score"],
            "triangle_qualified": bool(triangle and triangle.get("qualified")),
            "local_clusters": None if local is None else local["clusters"],
            "local_vortices": None if local is None else local["local_vortices"],
        })
    return {
        "trial_index": rec.get("trial_index"),
        "family": rec["family"],
        "knobs": rec["knobs"],
        "seed": rec["seed"],
        "triangle_seen": anchor is not None,
        "triangle": anchor,
        "strongest_triangle": strongest,
        "fission_like_after_triangle": bool(fission_like),
        "series": series,
        "honesty": {
            "triangle_was_seeded": False,
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
    rng = random.Random(seed ^ 0xA371)
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
    splits = [p for p in triangles if p.get("fission_like_after_triangle")]
    strongest = None
    for p in probes:
        tri = p.get("strongest_triangle")
        if tri and (strongest is None or tri.get("triangle_score", 0) > strongest.get("triangle_score", 0)):
            strongest = {**tri, "trial_index": p.get("trial_index"), "family": p.get("family"), "seed": p.get("seed")}
    return {
        "probed": len(probes),
        "triangle_seen": len(triangles),
        "fission_like_after_triangle": len(splits),
        "triangle_without_fission": max(0, len(triangles) - len(splits)),
        "rate_given_triangle": round(len(splits) / len(triangles), 4) if triangles else None,
        "strongest_triangle": strongest,
        "note": "A fission-like event is a later split of the nearby vortex cluster, not biological cell division.",
    }


def update_triangle_hypothesis(doc: dict[str, Any], *, burst_id: str, summary: dict[str, Any]) -> dict[str, Any]:
    hypotheses = doc.setdefault("hypotheses", [])
    h = next((x for x in hypotheses if x.get("id") == "three-vortex-triangle-fission"), None)
    if h is None:
        h = {
            "id": "three-vortex-triangle-fission",
            "statement": "When three naturally formed vortices make a robust triangle, a nearby structure may later split into separate groups more often.",
            "counter_statement": "The triangle is only a coincidence; later splitting is no more likely than in other vortex arrangements.",
            "falsification_condition": "Many naturally observed triangles are followed by no excess of persistent split-like geometry compared with controls.",
            "status": "TESTING", "support": 0, "contradiction": 0,
            "support_cycles": [], "confidence": 0.5,
        }
        hypotheses.append(h)
    positive = int(summary.get("fission_like_after_triangle", 0))
    negative = int(summary.get("triangle_without_fission", 0))
    h["support"] = int(h.get("support", 0)) + positive
    h["contradiction"] = int(h.get("contradiction", 0)) + negative
    cycles = set(h.get("support_cycles") or [])
    if positive:
        cycles.add(burst_id)
    h["support_cycles"] = sorted(cycles)
    s, c = int(h["support"]), int(h["contradiction"])
    cap = 0.65 if len(cycles) < 2 else 0.85
    h["confidence"] = round(min(cap, max(0.15, (s + 1) / (s + c + 2))), 4)
    if s >= 2 and c >= 2:
        h["status"] = "UNCERTAIN"
    elif s >= 2:
        h["status"] = "SUPPORTED"
    elif c >= 3 and s == 0:
        h["status"] = "WEAKENED"
    else:
        h["status"] = "TESTING"
    h["last_burst"] = burst_id
    _HYPOTHESES.parent.mkdir(parents=True, exist_ok=True)
    _HYPOTHESES.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    return doc


def write_easy_report(
    report: dict[str, Any], *, geometry: dict[str, Any], director_refreshed: bool, stamp: str,
) -> dict[str, str]:
    """Write a jargon-light report after every hourly experiment burst."""
    c = report.get("counts") or {}
    native = ((report.get("adaptive_research") or {}).get("native_3d") or {})
    reproduced = int(c.get("reproduced", 0))
    dimension_hits = int(native.get("dimension_emergence", 0))
    triangles = int(geometry.get("triangle_seen", 0))
    splits = int(geometry.get("fission_like_after_triangle", 0))
    new_regions = int(((report.get("adaptive_research") or {}).get("coverage_progress") or {}).get("new_regions", 0))

    if splits:
        one_line = f"3つの渦が三角っぽく並んだあと、近くのまとまりが分かれるような変化を {splits} 件見つけました。"
    elif triangles:
        one_line = f"3つの渦が三角っぽく並ぶ場面を {triangles} 件見つけましたが、その後の分かれる変化はまだ確認できませんでした。"
    elif reproduced:
        one_line = f"やり直しても似た結果になった条件が {reproduced} 件ありました。"
    else:
        one_line = "今回は大きな発見はありませんでしたが、まだ調べていなかった場所を広げました。"

    easy = {
        "version": 1,
        "burst_id": report.get("burst_id"),
        "generated_at": report.get("generated_at"),
        "one_line": one_line,
        "what_we_did": f"平面の世界で {int(c.get('mass_2d_trials', 0)):,} 通り、立体の世界で {int(c.get('native_3d_trials', 0)):,} 通りを試しました。",
        "what_we_found": (
            f"別の偶然の並びでも似た結果になった候補は {reproduced} 件。"
            f" 立体から始めた方が強かった候補は {dimension_hits} 件。"
            f" 新しく調べた範囲は {new_regions} 区画です。"
        ),
        "triangle_question": (
            f"詳しく追いかけた {int(geometry.get('probed', 0))} 件のうち、3つの渦が三角っぽく並んだものは {triangles} 件。"
            f" そのあと近くのまとまりが2つ以上に分かれたように見えたものは {splits} 件です。"
        ),
        "what_next": (
            "今回の結果をまとめて、次にどこを多めに調べるかを考え直しました。"
            if director_refreshed else
            "今の調べ方はまだ変えず、次の大きな見直しまで同じ方針でデータを増やします。"
        ),
        "important_note": "ここでいう「分かれた」は細胞分裂そのものではありません。まずは形の変化として数え、何度も同じ順番で起きるかを確かめます。",
        "director_refreshed": bool(director_refreshed),
        "geometry_summary": geometry,
    }
    out = _EASY / stamp
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "report.json"
    md_path = out / "report.md"
    json_path.write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    md = "\n".join([
        "# やさしい実験レポート",
        "",
        f"**ひとことで：** {easy['one_line']}",
        "",
        "## 今回なにをした？",
        easy["what_we_did"],
        "",
        "## なにが分かった？",
        easy["what_we_found"],
        "",
        "## 3つの渦の三角形は？",
        easy["triangle_question"],
        "",
        "## 次は？",
        easy["what_next"],
        "",
        f"> {easy['important_note']}",
        "",
    ])
    md_path.write_text(md)
    _EASY.mkdir(parents=True, exist_ok=True)
    (_EASY / "latest.json").write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    (_EASY / "latest.md").write_text(md)
    return {"json": str(json_path), "markdown": str(md_path), "latest": str(_EASY / "latest.json")}
