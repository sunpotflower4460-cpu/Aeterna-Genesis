"""Strict geometry lane + observation-only 0->fission path.

Triangles are never seeded.  This module watches naturally formed mutual-nearest vortex triads,
keeps matched non-triangle controls, and now also asks a second competing question: is a later split
better predicted by the LOSS of a previously balanced triangle than by triangle presence itself?

Nothing here changes the field law, official Emergence Levels, success thresholds, or promotion gates.
"""
from __future__ import annotations

import json
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from ai_lab import lab
from ai_lab.dream import fission_path
from genesis.diagnostics import geometry_events as geom
from genesis.models import ginzburg_landau as gl

_REPO = Path(__file__).resolve().parents[2]
_HYPOTHESES = _REPO / "ai_lab" / "discoveries" / "hypothesis_ledger.json"
_EASY = _REPO / "ai_lab" / "reports" / "easy"


def _persistent_anchor(
    snapshots: list[dict[str, Any]], *, kind: str, shape: tuple[int, int]
) -> tuple[int, dict[str, Any]] | None:
    """Find the first same local relation observed in two consecutive snapshots."""
    key = {"triangle": "triangle", "control": "control", "relation": "triad"}[kind]
    for i in range(1, len(snapshots)):
        a = snapshots[i - 1].get(key)
        b = snapshots[i].get(key)
        if a and b and geom.same_local_triad(a, b, shape):
            return i - 1, {**a, "step": snapshots[i - 1]["step"], "persistence_snapshots": 2}
    return None


def _split_after(
    snapshots: list[dict[str, Any]], anchor_index: int, anchor: dict[str, Any], shape: tuple[int, int]
) -> bool:
    """Legacy matched outcome: nearby vortex relation later persists as 2+ connected groups."""
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


def _near_anchor(triad: dict[str, Any] | None, anchor: dict[str, Any], shape: tuple[int, int]) -> bool:
    if not triad:
        return False
    max_side = max(float(anchor.get("max_side") or 1.0), float(triad.get("max_side") or 1.0))
    return geom.periodic_distance(triad["centroid"], anchor["centroid"], shape) <= max(2.0, 0.75 * max_side)


def _triangle_transition_after(
    snapshots: list[dict[str, Any]], anchor_index: int, anchor: dict[str, Any], shape: tuple[int, int]
) -> dict[str, Any]:
    """Observe balanced triangle -> imbalance while connected -> persistent relation split.

    This is intentionally a relation-network detector, not a cell-body detector.  Requiring the
    imbalance to occur while the local vortices are still ONE connected group prevents us from
    calling an already-separated control arrangement a pre-division instability.
    """
    max_side = max(float(x) for x in anchor["side_lengths"])
    neighbourhood = max(4.0, 1.8 * max_side)
    link = max(2.0, 1.05 * max_side)
    base_reg = float(anchor.get("regularity") or 0.0)
    base_area = float(anchor.get("area_ratio") or 0.0)

    collapse_streak = 0
    one_group_streak = 0
    split_streak = 0
    collapse_seen = False
    pre_split_instability = False
    split_seen = False
    collapse_step = None
    split_step = None

    for snap in snapshots[anchor_index + 2:]:
        local = geom.local_cluster_count(
            snap["points"], centre=anchor["centroid"], shape=shape,
            neighbourhood_radius=neighbourhood, link_radius=link,
        )
        triad = snap.get("triad")
        tracked = triad if _near_anchor(triad, anchor, shape) else None
        connected_one = local["local_vortices"] >= 3 and local["clusters"] == 1

        # Balance loss can be measured either as a substantial geometry change of the same local
        # mutual triad, or as persistent loss of the strict triangle qualification while the local
        # relation is still one connected group.
        reg_drop = 0.0 if not tracked else base_reg - float(tracked.get("regularity") or 0.0)
        area_drop = 0.0 if not tracked else base_area - float(tracked.get("area_ratio") or 0.0)
        balance_lost = bool(
            connected_one
            and (
                reg_drop >= 0.12
                or area_drop >= 0.08
                or not bool(snap.get("triangle"))
            )
        )
        snap["path_local"] = local
        snap["path_tracked_triad"] = tracked
        snap["path_balance_lost"] = balance_lost

        if balance_lost:
            collapse_streak += 1
        else:
            collapse_streak = 0
        if collapse_streak >= 2 and not collapse_seen:
            collapse_seen = True
            collapse_step = snap["step"]

        if collapse_seen and connected_one:
            one_group_streak += 1
            if one_group_streak >= 2:
                pre_split_instability = True
        elif not connected_one:
            one_group_streak = 0

        if local["local_vortices"] >= 2 and local["clusters"] >= 2:
            split_streak += 1
            if split_streak >= 2:
                split_seen = True
                split_step = snap["step"]
                break
        else:
            split_streak = 0

    return {
        "balance_collapse_seen": collapse_seen,
        "balance_collapse_step": collapse_step,
        "pre_split_instability_candidate": pre_split_instability,
        "persistent_split_seen": split_seen,
        "persistent_split_step": split_step,
        "network_fission_candidate": bool(collapse_seen and pre_split_instability and split_seen),
        "network_fission_is_biological_cell_division": False,
    }


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
            "triad": geom.best_mutual_triad(points, shape),
            "triangle": geom.best_triangle(points, shape),
            "control": geom.best_control_triad(points, shape),
        })

    relation_found = _persistent_anchor(snapshots, kind="relation", shape=shape)
    # A run is a triangle case if a persistent triangle exists. Only runs without one may become
    # non-triangle controls; this prevents the same run from being counted on both sides.
    tri_found = _persistent_anchor(snapshots, kind="triangle", shape=shape)
    ctrl_found = None if tri_found else _persistent_anchor(snapshots, kind="control", shape=shape)
    category = "triangle" if tri_found else ("control" if ctrl_found else None)
    found = tri_found or ctrl_found
    anchor_index, anchor = found if found else (None, None)
    split = bool(found and _split_after(snapshots, int(anchor_index), anchor, shape))
    transition = (
        _triangle_transition_after(snapshots, int(tri_found[0]), tri_found[1], shape)
        if tri_found else {
            "balance_collapse_seen": False,
            "balance_collapse_step": None,
            "pre_split_instability_candidate": False,
            "persistent_split_seen": False,
            "persistent_split_step": None,
            "network_fission_candidate": False,
            "network_fission_is_biological_cell_division": False,
        }
    )

    compact_series = []
    for s in snapshots:
        triad = s.get("triad") or {}
        local = s.get("path_local") or {}
        compact_series.append({
            "step": s["step"],
            "vortices": len(s["points"]),
            "relation": bool(s.get("triad")),
            "triangle": bool(s.get("triangle")),
            "control": bool(s.get("control")),
            "regularity": triad.get("regularity"),
            "area_ratio": triad.get("area_ratio"),
            "charge_pattern": triad.get("charge_pattern"),
            "local_clusters": local.get("clusters"),
            "local_vortices": local.get("local_vortices"),
            "balance_lost": bool(s.get("path_balance_lost")),
        })

    out = {
        "trial_index": rec.get("trial_index"),
        "family": rec["family"], "knobs": rec["knobs"], "seed": rec["seed"],
        "reached_level": rec.get("reached_level"),
        "triad_type": category,
        "persistent_relation_seen": relation_found is not None,
        "relation": None if relation_found is None else relation_found[1],
        "triangle_seen": category == "triangle",
        "control_seen": category == "control",
        "triangle": anchor if category == "triangle" else None,
        "control": anchor if category == "control" else None,
        "fission_like_after_triangle": bool(category == "triangle" and split),
        "fission_like_after_control": bool(category == "control" and split),
        **transition,
        "series": compact_series,
        "honesty": {
            "triangle_was_seeded": False,
            "division_site_or_time_seeded": False,
            "persistent_two_snapshots_required": True,
            "mutual_nearest_triad_required": True,
            "matched_nontriangle_control": True,
            "fission_like_is_biological_cell_division": False,
            "network_fission_is_biological_cell_division": False,
            "changes_level_gate": False,
        },
    }
    out["zero_to_fission"] = fission_path.assess_probe(out)
    return out


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

    collapsed = [p for p in triangles if p.get("balance_collapse_seen")]
    uncollapsed = [p for p in triangles if not p.get("balance_collapse_seen")]
    collapsed_splits = [p for p in collapsed if p.get("fission_like_after_triangle")]
    uncollapsed_splits = [p for p in uncollapsed if p.get("fission_like_after_triangle")]
    collapse_rate = len(collapsed_splits) / len(collapsed) if collapsed else None
    no_collapse_rate = len(uncollapsed_splits) / len(uncollapsed) if uncollapsed else None
    collapse_excess = None if collapse_rate is None or no_collapse_rate is None else collapse_rate - no_collapse_rate

    return {
        "detector_version": 3,
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
        "balance_collapse_seen": len(collapsed),
        "split_after_balance_collapse": len(collapsed_splits),
        "triangle_without_balance_collapse": len(uncollapsed),
        "split_without_balance_collapse": len(uncollapsed_splits),
        "rate_given_balance_collapse": None if collapse_rate is None else round(collapse_rate, 4),
        "rate_without_balance_collapse": None if no_collapse_rate is None else round(no_collapse_rate, 4),
        "balance_collapse_excess_rate": None if collapse_excess is None else round(collapse_excess, 4),
        "balance_comparison_ready": bool(len(collapsed) >= 3 and len(uncollapsed) >= 3),
        "pre_split_instability_candidates": sum(bool(p.get("pre_split_instability_candidate")) for p in probes),
        "network_fission_candidates": sum(bool(p.get("network_fission_candidate")) for p in probes),
        "zero_to_fission_path": fission_path.summarize(probes),
        "note": (
            "Only persistent mutual-nearest triads count. Relation-network fission is an observation "
            "candidate, not biological cell division or official Emergence Level 7."
        ),
    }


def _update_binary_burst_hypothesis(
    h: dict[str, Any], *, burst_id: str, ready: bool, excess: float | None
) -> None:
    if ready:
        h["comparison_bursts"] = int(h.get("comparison_bursts", 0)) + 1
        x = float(excess or 0.0)
        if x >= 0.10:
            h["support"] = int(h.get("support", 0)) + 1
            cycles = set(h.get("support_cycles") or [])
            cycles.add(burst_id)
            h["support_cycles"] = sorted(cycles)
        elif x <= 0.02:
            h["contradiction"] = int(h.get("contradiction", 0)) + 1
    s, c = int(h.get("support", 0)), int(h.get("contradiction", 0))
    cycles = h.get("support_cycles") or []
    cap = 0.65 if len(cycles) < 2 else 0.85
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


def update_triangle_hypothesis(doc: dict[str, Any], *, burst_id: str, summary: dict[str, Any]) -> dict[str, Any]:
    hypotheses = doc.setdefault("hypotheses", [])

    apparatus = next((x for x in hypotheses if x.get("id") == "three-vortex-triangle-fission"), None)
    if apparatus is None:
        apparatus = {
            "id": "three-vortex-triangle-fission",
            "statement": "A persistent isolated three-vortex triangle may act as a fission apparatus and be followed by local splitting more often than a non-triangular triad.",
            "counter_statement": "Triangle shape is incidental or stabilizing; its later split rate is not higher than matched non-triangle triads.",
            "falsification_condition": "Across repeated bursts, triangle split rate fails to exceed the matched-control split rate.",
            "status": "TESTING", "support": 0, "contradiction": 0,
            "support_cycles": [], "confidence": 0.5, "comparison_bursts": 0,
        }
        hypotheses.append(apparatus)
    _update_binary_burst_hypothesis(
        apparatus, burst_id=burst_id, ready=bool(summary.get("comparison_ready")),
        excess=summary.get("triangle_excess_rate"),
    )
    apparatus["last_comparison"] = {
        k: summary.get(k) for k in (
            "triangle_seen", "fission_like_after_triangle", "control_seen",
            "fission_like_after_control", "rate_given_triangle", "rate_given_control",
            "triangle_excess_rate", "comparison_ready",
        )
    }

    balance = next((x for x in hypotheses if x.get("id") == "triangle-balance-break-fission"), None)
    if balance is None:
        balance = {
            "id": "triangle-balance-break-fission",
            "statement": "A persistent triangle may be a temporary stable relation; loss of its balance while still connected may predict a later split better than triangle presence alone.",
            "counter_statement": "Apparent balance loss is incidental and does not increase later split probability.",
            "falsification_condition": "Across repeated matched triangle cases, collapse-before-split is no more predictive than triangles without measured collapse.",
            "status": "TESTING", "support": 0, "contradiction": 0,
            "support_cycles": [], "confidence": 0.5, "comparison_bursts": 0,
        }
        hypotheses.append(balance)
    _update_binary_burst_hypothesis(
        balance, burst_id=burst_id, ready=bool(summary.get("balance_comparison_ready")),
        excess=summary.get("balance_collapse_excess_rate"),
    )
    balance["last_comparison"] = {
        k: summary.get(k) for k in (
            "balance_collapse_seen", "split_after_balance_collapse",
            "triangle_without_balance_collapse", "split_without_balance_collapse",
            "rate_given_balance_collapse", "rate_without_balance_collapse",
            "balance_collapse_excess_rate", "balance_comparison_ready",
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
    path = geometry.get("zero_to_fission_path") or {}
    depth = int(path.get("deepest_contiguous_stage", -1))

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

    if depth >= 0:
        path_text = (
            f"『0から分裂への道』は、同じ実験の中で今のところ段階 {depth} "
            f"（{path.get('deepest_label')}）まで連続して確認できました。"
        )
        if depth < 7:
            best = path.get("best_frontier_candidate") or {}
            path_text += f" 次に確かめたいのは段階 {best.get('next_stage', depth + 1)}（{best.get('next_stage_label')}）です。"
        else:
            path_text += " ただし段階7はまだ『渦の関係網が分かれた候補』で、細胞分裂そのものではありません。"
    else:
        path_text = "今回は、厳しい『0から連続』条件で段階を進めた例はありませんでした。"

    collapse_n = int(geometry.get("balance_collapse_seen", 0))
    network_n = int(geometry.get("network_fission_candidates", 0))
    balance_text = (
        f"三角形ができた後に、まだ1つの集まりのままバランスが崩れた例は {collapse_n} 件。"
        f" その順序を経て2つ以上へ分かれた『関係網の分裂候補』は {network_n} 件でした。"
    )

    easy = {
        "version": 3, "burst_id": report.get("burst_id"), "generated_at": report.get("generated_at"),
        "one_line": one_line,
        "what_we_did": f"平面の世界で {int(c.get('mass_2d_trials', 0)):,} 通り、立体の世界で {int(c.get('native_3d_trials', 0)):,} 通りを試しました。",
        "what_we_found": f"やり直しても似た結果になった候補は {reproduced} 件。立体から始めた方が強かった候補は {dimension_hits} 件。新しく調べた範囲は {new_regions} 区画です。",
        "triangle_question": (
            f"今回は、3つが互いに近い仲間としてまとまり、その並びが続いた場合だけ数えました。"
            f" 三角の3つ組は {tn} 件（その後に分かれたように見えたのは {ts} 件）。"
            f" 三角ではない比較用の3つ組は {cn} 件（分かれたのは {cs} 件）でした。"
        ),
        "balance_break_question": balance_text,
        "zero_to_fission_question": path_text,
        "zero_to_fission_path": path,
        "what_next": "結果をまとめて次の調べ方を考え直しました。" if director_refreshed else "次の大きな見直しまで同じ方針で例を増やします。",
        "important_note": (
            "『分かれた』は細胞分裂そのものという意味ではありません。三角形も分裂位置も最初から置きません。"
            " 三角形そのものが効く説と、三角形のバランス崩壊が前兆だという説を両方比較します。"
        ),
        "director_refreshed": bool(director_refreshed), "geometry_summary": geometry,
    }
    out = _EASY / stamp
    out.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out / "report.json", out / "report.md"
    json_path.write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    md = "\n".join([
        "# やさしい実験レポート", "", f"**ひとことで：** {one_line}", "",
        "## 今回なにをした？", easy["what_we_did"], "", "## なにが分かった？", easy["what_we_found"], "",
        "## 0から分裂への道はどこまで進んだ？", path_text, "",
        "## 三角形のバランスが崩れると？", balance_text, "",
        "## 3つの渦の三角形は？", easy["triangle_question"], "", "## 次は？", easy["what_next"], "",
        f"> {easy['important_note']}", "",
    ])
    md_path.write_text(md)
    _EASY.mkdir(parents=True, exist_ok=True)
    (_EASY / "latest.json").write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    (_EASY / "latest.md").write_text(md)
    return {"json": str(json_path), "markdown": str(md_path), "latest": str(_EASY / "latest.json")}
