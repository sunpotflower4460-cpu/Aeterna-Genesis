#!/usr/bin/env python3
"""Catalog generator: build app/generated/catalog.{json,js} from Python-side metadata.

The Observatory App NEVER hard-codes experiment/room data (設計書 §17). This is the SINGLE source: it
reads rooms/catalog.json + rooms/official/*/room.yaml + experiments/*/experiment.yaml + docs/TRUST_MAP
counts, and emits catalog.json (+ catalog.js assigning window.CATALOG for file:// use).

Official 3D Rooms and 2D/AI candidates are kept DISTINCT (設計書 §23: AI 発見候補が正式 Room と混同されない).
Every render channel maps to a real measured physical quantity (render.yaml).
"""

import argparse
import json
import os
import sys

import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load_yaml(p):
    with open(p) as f:
        return yaml.safe_load(f)


def _genesis_knobs(g):
    """Flatten a genesis doc into the scalar start-side knobs that define the initial condition/protocol.
    This is exactly what a Live Runner / AI mutation is allowed to change, so diffing two of these gives
    an honest, complete 'what was put in differently' between a candidate and its parent."""
    if not g:
        return {}
    ist = g.get("initial_state", {}) or {}
    q = (g.get("protocol", {}) or {}).get("quench", {}) or {}
    knobs = {}
    for k in ("noise_amplitude", "correlation_length", "mean_amplitude"):
        if k in ist:
            knobs[k] = ist[k]
    if "duration" in q:
        knobs["quench_duration"] = q["duration"]
    if g.get("seed") is not None:
        knobs["seed"] = g.get("seed")
    return knobs


def _resolve_room_dir(room_id, room_index):
    """Locate a room dir by id across the official index + candidate/rejected trees."""
    for e in room_index:
        if e.get("room_id") == room_id:
            return os.path.join(_REPO, e["path"])
    for base in ("candidates", "rejected_in_3d"):
        d = os.path.join(_REPO, "rooms", base, room_id)
        if os.path.isdir(d):
            return d
    return None


# The promotion pipeline a candidate must climb to become an official 3D Room (DIMENSION_POLICY).
# A candidate NEVER self-promotes; this only reports how far measurement has actually carried it.
PROMOTION_STAGES = ["exploration_2d", "local_3d", "coarse_global_3d", "full_3d"]


def _promotion_stage(dstat, source):
    """Report the promotion pipeline honestly: which stages passed, the current front, and whether the
    candidate was rejected in 3D. Does not decide promotion -- only mirrors recorded dimension_status."""
    passed = [s for s in PROMOTION_STAGES if dstat.get(s) == "passed"]
    current = next((s for s in PROMOTION_STAGES if dstat.get(s) not in ("passed",)), "full_3d")
    return {
        "stages": [{"name": s, "status": dstat.get(s, "not_started")} for s in PROMOTION_STAGES],
        "passed": passed,
        "current": current,
        "rejected_in_3d": source == "rejected_in_3d",
        "is_official": False,  # a candidate is never official; promotion is a separate gated step
    }


def _genesis_diff(parent_room, cand_genesis, room_index):
    """Honest diff: which start-side knobs differ between a candidate and its parent, from the genesis
    docs themselves (not a stored label). Returns {knob: {from, to}} plus parent reached level."""
    diff, parent_level = {}, None
    pdir = _resolve_room_dir(parent_room, room_index) if parent_room else None
    if pdir:
        pg = os.path.join(pdir, "genesis.yaml")
        parent_knobs = _genesis_knobs(_load_yaml(pg)) if os.path.exists(pg) else {}
        cand_knobs = _genesis_knobs(cand_genesis)
        for k in sorted(set(parent_knobs) | set(cand_knobs)):
            pv, cv = parent_knobs.get(k), cand_knobs.get(k)
            if pv != cv:
                diff[k] = {"from": pv, "to": cv}
        pr = os.path.join(pdir, "room.yaml")
        if os.path.exists(pr):
            parent_level = (_load_yaml(pr).get("emergence") or {}).get("reached_level")
    return diff, parent_level


def build():
    # rooms
    rooms = []
    rc_path = os.path.join(_REPO, "rooms", "catalog.json")
    room_index = json.load(open(rc_path))["rooms"] if os.path.exists(rc_path) else []
    for entry in room_index:
        rdir = os.path.join(_REPO, entry["path"])
        room_yaml = _load_yaml(os.path.join(rdir, "room.yaml")) if os.path.exists(os.path.join(rdir, "room.yaml")) else {}
        genesis = _load_yaml(os.path.join(rdir, "genesis.yaml")) if os.path.exists(os.path.join(rdir, "genesis.yaml")) else {}
        emergence = json.load(open(os.path.join(rdir, "emergence.json"))) if os.path.exists(os.path.join(rdir, "emergence.json")) else {}
        conv = json.load(open(os.path.join(rdir, "convergence.json"))) if os.path.exists(os.path.join(rdir, "convergence.json")) else {}
        render = _load_yaml(os.path.join(rdir, "render.yaml")) if os.path.exists(os.path.join(rdir, "render.yaml")) else {}
        rm_path = os.path.join(rdir, "render-manifest.yaml")
        rmf = _load_yaml(rm_path) if os.path.exists(rm_path) else {}
        runs = []
        runs_dir = os.path.join(rdir, "runs")
        if os.path.isdir(runs_dir):
            for sd in sorted(os.listdir(runs_dir)):
                mp = os.path.join(runs_dir, sd, "manifest.json")
                sp = os.path.join(runs_dir, sd, "summary.json")
                if os.path.exists(mp):
                    man = json.load(open(mp))
                    summ = json.load(open(sp)) if os.path.exists(sp) else {}
                    runs.append({"seed": man.get("seed"), "grid": man["manifest"]["grid"],
                                 "reached_level": summ.get("reached_level"),
                                 "checksum": man["checksum"]["final_field_sha256"][:12]})
        rooms.append({
            "room_id": entry["room_id"], "title": entry.get("title"), "official": bool(entry.get("official")),
            "kind": "official_3d_room", "parent_room": room_yaml.get("parent_room"),
            "genesis_model": entry.get("genesis_model"),
            "dimension": entry.get("dimension"),
            "reached_level": room_yaml.get("emergence", {}).get("reached_level", entry.get("reached_level")),
            "candidate_level": room_yaml.get("emergence", {}).get("candidate_level"),
            "physics_status": room_yaml.get("physics_status", {}),
            "dimension_status": room_yaml.get("dimension_status", {}),
            "measured_by": emergence.get("measured_by", {}),
            "convergence": {"level_converged": conv.get("level_converged"),
                            "reproducible": conv.get("reproducible_checksum"),
                            "free_energy_monotone": conv.get("free_energy_monotone_post_quench"),
                            "rows": conv.get("rows", [])},
            "natural_emergence": emergence.get("natural_emergence", {}),
            "render_map": render.get("mapping", {}),
            # Phase 0: references to recorded fields + render-manifest (NOT the data itself; §3 参照構造)
            "render_manifest": ("render-manifest.yaml" if rmf else None),
            "frames_ref": rmf.get("frames_ref"),
            "lenses": [l["lens"] for l in rmf.get("lenses", [])],
            "runs": runs,
            "put_in": entry.get("put_in",
                                "一様に近い無秩序＋微小ノイズ＋TDGLクエンチ（欠陥/パターンは入れない）"),
            "emerged": entry.get("emerged",
                                 "対称性破れ（秩序変数）＋位相巻き渦線（Kibble-Zurek）"),
        })

    # evidence library role counts (from experiment.yaml — the primary metadata)
    role_counts = {}
    genesis_roles = {}
    exp_dir = os.path.join(_REPO, "experiments")
    experiments = []
    if os.path.isdir(exp_dir):
        for d in sorted(x for x in os.listdir(exp_dir) if x.startswith("e0")):
            yp = os.path.join(exp_dir, d, "experiment.yaml")
            if not os.path.exists(yp):
                continue
            e = _load_yaml(yp)
            role = e.get("role", {}).get("primary")
            role_counts[role] = role_counts.get(role, 0) + 1
            gr = e.get("genesis_role")
            genesis_roles[gr] = genesis_roles.get(gr, 0) + 1
            experiments.append({"id": e.get("id"), "title": e.get("title"), "role": role,
                                "confidence": e.get("confidence"), "genesis_role": gr,
                                "target_encoded": e.get("target_encoded"),
                                "dimension": e.get("dimension", {}).get("computed")})

    # AI Genesis Lab discoveries (ledger) + candidate/rejected rooms -- kept DISTINCT from official rooms
    ai_candidates = []
    ledger_path = os.path.join(_REPO, "ai_lab", "discoveries", "ledger.json")
    if os.path.exists(ledger_path):
        led = json.load(open(ledger_path))
        for d in led.get("discoveries", []):
            ai_candidates.append({
                "key": d["key"], "kind": "ai_candidate", "parent_room": d.get("parent_room"),
                "mutation": d.get("mutation"), "screen_2d_level": d.get("screen_2d", {}).get("reached_level"),
                "delta_vs_parent": d.get("vs_parent", {}).get("delta_level"),
                "dimension_transfer_risk": d.get("dimension_transfer_risk"),
                "stage": d.get("stage"),
                "local_3d": d.get("local_3d"),
            })
    candidate_rooms = []
    for base in ("candidates", "rejected_in_3d"):
        bdir = os.path.join(_REPO, "rooms", base)
        if not os.path.isdir(bdir):
            continue
        for room in sorted(x for x in os.listdir(bdir) if os.path.isdir(os.path.join(bdir, x))):
            ry = os.path.join(bdir, room, "room.yaml")
            if not os.path.exists(ry):
                continue
            r = _load_yaml(ry)
            rm_path = os.path.join(bdir, room, "render-manifest.yaml")
            rmf = _load_yaml(rm_path) if os.path.exists(rm_path) else {}
            cg_path = os.path.join(bdir, room, "genesis.yaml")
            cand_genesis = _load_yaml(cg_path) if os.path.exists(cg_path) else {}
            diff, parent_level = _genesis_diff(r.get("parent_room"), cand_genesis, room_index)
            reached = r.get("emergence", {}).get("reached_level")
            dstat = r.get("dimension_status", {})
            candidate_rooms.append({
                "room_id": r.get("room_id"), "title": r.get("title"), "kind": "candidate_room",
                "official": False, "parent_room": r.get("parent_room"), "status": r.get("status"),
                "genesis_model": r.get("genesis_model"),
                "reached_level": reached,
                "candidate_level": r.get("emergence", {}).get("candidate_level"),
                "dimension_status": dstat,
                "physics_status": r.get("physics_status", {}),
                # Live Runner candidates carry recorded replay fields, same reference structure as rooms.
                "render_manifest": ("render-manifest.yaml" if rmf else None),
                "frames_ref": rmf.get("frames_ref"),
                "lenses": [l["lens"] for l in rmf.get("lenses", [])],
                "source": base,  # "candidates" (live/AI screen) or "rejected_in_3d"
                # Discovery Inbox (Phase 4): honest parent diff + promotion pipeline stage.
                "diff_vs_parent": diff,
                "parent_reached_level": parent_level,
                "delta_level": (reached - parent_level) if (reached is not None and parent_level is not None) else None,
                "promotion": _promotion_stage(dstat, base),
            })

    # Live Runner jobs (Phase 3): UI-requested jobs executed by tools/run_job.py. The browser never runs
    # physics; the ledger + per-job status files record what the worker actually computed. A job's
    # result_room is a candidate room above -- a job can never self-promote to an official room.
    jobs = []
    jobs_dir = os.path.join(_REPO, "rooms", "jobs")
    led_p = os.path.join(jobs_dir, "ledger.json")
    if os.path.exists(led_p):
        for j in json.load(open(led_p)).get("jobs", []):
            jid = j.get("job_id")
            sp = os.path.join(jobs_dir, "%s.json" % jid)
            status = json.load(open(sp)) if os.path.exists(sp) else j
            jobs.append({
                "job_id": jid, "parent_room": j.get("parent_room"), "override": j.get("override"),
                "seed": j.get("seed"), "status": status.get("status", j.get("status")),
                "progress": status.get("progress"), "result_room": j.get("result_room"),
                "reached_level": j.get("reached_level"), "checksum": j.get("checksum"),
                "measured_by": status.get("measured_by", {}),
            })

    catalog = {
        "catalog_version": 1,
        "generated_from": "rooms/catalog.json + rooms/official/*/ + rooms/candidates/* + "
                          "ai_lab/discoveries/ledger.json + experiments/*/experiment.yaml",
        "note": "Observatory App の唯一の表示元。ハードコードしない。official 3D Room と AI 候補/候補Room は区別。",
        "rooms": rooms,
        "evidence_library": {"count": len(experiments), "role_counts": role_counts,
                             "genesis_roles": genesis_roles, "experiments": experiments},
        "ai_candidates": ai_candidates,      # AI Lab 2D-screened discoveries (ledger) -- DISTINCT from rooms
        "candidate_rooms": candidate_rooms,  # local-3D 昇格した非公式候補 -- official ではない
        "jobs": jobs,                        # Live Runner ジョブ台帳（UIが依頼→Python worker が実計算）
    }
    return catalog


def write(catalog, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "catalog.json"), "w") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out_dir, "catalog.js"), "w") as f:
        f.write("// Auto-generated by tools/build_catalog.py. Do not edit. window.CATALOG for file:// use.\n")
        f.write("window.CATALOG = ")
        json.dump(catalog, f, indent=2, ensure_ascii=False)
        f.write(";\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the Observatory App catalog from Python-side metadata")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out-dir", default=os.path.join(_REPO, "app", "generated"))
    args = ap.parse_args(argv)
    cat = build()
    print("=== catalog: %d room(s), %d evidence experiments ==="
          % (len(cat["rooms"]), cat["evidence_library"]["count"]))
    print("  role_counts:", cat["evidence_library"]["role_counts"])
    for r in cat["rooms"]:
        print("  room %s: %s, reached_level=%s, physics=%s"
              % (r["room_id"], r["dimension"], r["reached_level"],
                 "all-passed" if all(v == "passed" for v in r["physics_status"].values()) else r["physics_status"]))
    if not args.no_write:
        write(cat, args.out_dir)
        print("  wrote %s/catalog.{json,js}" % os.path.relpath(args.out_dir, _REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
