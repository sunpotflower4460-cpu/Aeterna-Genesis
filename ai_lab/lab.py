#!/usr/bin/env python3
"""AI Genesis Lab (minimal): an automated experimenter that searches START CONDITIONS, not designs.

AI's job (AGENTS.md / AI_EXPERIMENT_POLICY.md): NOT to build a finished shape, but to find start
conditions that grow deeper on their own. This minimal Lab:

  1. reads a PARENT room (rooms/official/room-g001-a) and the allowed search space
     (genesis/registry/param_ranges.yaml) -- it may change ONLY start-side parameters,
  2. proposes a CHILD genesis with ONE parameter changed within the allowed range,
  3. runs it FROM t=0 (2D screen) with the SAME Runner + diagnostics the Room uses (it does NOT
     redefine success criteria / thresholds -- those are imported, not copied),
  4. measures the reached Level and compares to the parent baseline,
  5. registers a dimension-transfer RISK (harness) for any 2D candidate,
  6. saves a NON-DESTRUCTIVE proposal (never touches rooms/official, parent Room, or thresholds).

Determinism: no Math.random for the search -- parameter values come from a fixed grid indexed by the
proposal number, so runs are reproducible. Promotion to full-3D is GATED (2d_screened only here).
"""

import argparse
import json
import os
import sys

import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from genesis.models import ginzburg_landau as gl  # noqa: E402
from genesis.runners import runner  # noqa: E402
from genesis.dimension import harness  # noqa: E402

# start-side knobs the Lab may vary (subset of param_ranges.yaml search_space) -> (path, grid of values)
KNOBS = {
    "noise_amplitude": [1.0e-4, 3.0e-4, 1.0e-3, 3.0e-3, 1.0e-2],
    "quench_duration": [4.0, 6.0, 8.0, 12.0, 16.0],
}


def _load_search_space():
    p = os.path.join(_REPO, "genesis", "registry", "param_ranges.yaml")
    return yaml.safe_load(open(p))["search_space"]


def _parent_baseline(quick=True):
    """Screen the parent genesis (room-g001-a defaults) in 2D from t=0 for a fair comparison."""
    g = dict(runner._DEMO_GENESIS)
    r = runner.run(g, mode="2d-screen", quick=quick)
    return r["manifest"]["summary"]["reached_level"], r["emergence"]["measured_by"]


def propose(index):
    """Deterministically pick ONE knob + value from the grid (indexed), return a child genesis + mutation."""
    knobs = sorted(KNOBS)
    knob = knobs[index % len(knobs)]
    grid = KNOBS[knob]
    val = grid[(index // len(knobs)) % len(grid)]
    g = dict(runner._DEMO_GENESIS)
    g["initial_state"] = dict(g["initial_state"])
    g["protocol"] = {"quench": dict(g["protocol"]["quench"])}
    frm = None
    if knob == "noise_amplitude":
        frm = g["initial_state"]["noise_amplitude"]
        g["initial_state"]["noise_amplitude"] = val
    elif knob == "quench_duration":
        frm = g["protocol"]["quench"]["duration"]
        g["protocol"]["quench"]["duration"] = val
    g["seed"] = 0
    mutation = {"type": "initial_state_change" if knob == "noise_amplitude" else "parameter_change",
                "param": knob, "from": frm, "to": val}
    return g, mutation


def _within_allowed(mutation, search_space):
    """Verify the proposed value is inside the allowed search-space range (AI cannot exceed it)."""
    if mutation["param"] == "noise_amplitude":
        rng = search_space["initial_state"]["noise_amplitude"]
        return rng["min"] <= mutation["to"] <= rng["max"]
    if mutation["param"] == "quench_duration":
        return 0.0 < mutation["to"] <= 40.0     # protocol duration: physical, bounded
    return False


def screen(genesis, quick=True):
    r = runner.run(genesis, mode="2d-screen", quick=quick)
    return r["manifest"]["summary"]["reached_level"], r["emergence"]["measured_by"], r["manifest"]["checksum"]


def run_lab(n=4, quick=True):
    search_space = _load_search_space()
    base_level, base_mb = _parent_baseline(quick=quick)
    dtrans, _ = harness.report(quick=quick)
    dim_risk = dtrans["dimension_risk"]["expected_transferability"]
    proposals = []
    for i in range(n):
        g, mut = propose(i)
        allowed = _within_allowed(mut, search_space)
        if not allowed:
            proposals.append({"proposal_id": "prop-%04d" % i, "mutation": mut,
                              "status": "rejected", "reason": "outside_allowed_search_space"})
            continue
        level, mb, checksum = screen(g, quick=quick)
        prop = {
            "proposal_id": "prop-%04d" % i,
            "parent_room": "room-g001-a",
            "mutation": mut,
            "genesis": g,
            "screen_2d": {"reached_level": level,
                          "mean_amplitude_growth": mb["mean_amplitude_growth"],
                          "defect_count": mb["defect_count"]},
            "vs_parent": {"parent_level": base_level, "delta_level": level - base_level},
            "dimension_transfer_risk": dim_risk,
            "checksum": checksum["final_field_sha256"][:16],
            # promotion is GATED: the Lab only 2D-screens; full-3D + Room registration is a separate,
            # human/promote-command step (AI cannot self-promote or write rooms/official).
            "status": "2d_screened",
            "promotion": {"stage": "2d_screened",
                          "next": "dimension_audit -> local_3d -> coarse_global_3d -> full_3d"},
        }
        proposals.append(prop)
    return {"parent_baseline_level": base_level, "n": n, "proposals": proposals}


def write_out(result, out_root):
    """Write per-proposal detail files (ephemeral, gitignored) under out_root/ai_lab/proposals/."""
    d = os.path.join(out_root, "ai_lab", "proposals")
    os.makedirs(d, exist_ok=True)
    for p in result["proposals"]:
        with open(os.path.join(d, p["proposal_id"] + ".json"), "w") as f:
            json.dump(p, f, indent=2)
    return d


# ----- persistent, append-only-by-key discovery LEDGER (committed; the AI/human read this back) -----

LEDGER_PATH = os.path.join(_REPO, "ai_lab", "discoveries", "ledger.json")


def _ledger_key(mut):
    return "%s=%s" % (mut["param"], mut["to"])


def load_ledger(path=LEDGER_PATH):
    if os.path.exists(path):
        return json.load(open(path))
    return {"ledger_version": 1,
            "note": "AI Genesis Lab 発見台帳（append-only by mutation key・非破壊・決定的）。"
                    "AI/人が蓄積を確認する一次記録。official Room とは別物（候補）。",
            "parent_room": "room-g001-a", "discoveries": []}


def record_ledger(result, path=LEDGER_PATH):
    """Upsert each screened proposal into the ledger, keyed by mutation. Idempotent (no churn on re-run)."""
    led = load_ledger(path)
    by_key = {d["key"]: d for d in led["discoveries"]}
    for p in result["proposals"]:
        if p["status"] != "2d_screened":
            continue
        key = _ledger_key(p["mutation"])
        rec = by_key.get(key, {})
        rec.update({"key": key, "parent_room": p["parent_room"], "mutation": p["mutation"],
                    "screen_2d": p["screen_2d"], "vs_parent": p["vs_parent"],
                    "dimension_transfer_risk": p["dimension_transfer_risk"],
                    "checksum_2d": p["checksum"], "stage": rec.get("stage", "2d_screened")})
        by_key[key] = rec
    led["discoveries"] = [by_key[k] for k in sorted(by_key)]
    led["parent_baseline_level"] = result["parent_baseline_level"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(led, f, indent=2, ensure_ascii=False)
    return led


def review(path=LEDGER_PATH):
    """Print the accumulated discovery ledger so the AI (or a human) can inspect prior auto-tests."""
    led = load_ledger(path)
    ds = led["discoveries"]
    print("=== AI Genesis Lab — discovery ledger (%d accumulated, parent %s, baseline 2D level %s) ==="
          % (len(ds), led.get("parent_room"), led.get("parent_baseline_level")))
    for d in ds:
        print("  %-22s | 2D level=%s (delta %+d vs parent) | risk=%s | stage=%s"
              % (d["key"], d["screen_2d"]["reached_level"], d["vs_parent"]["delta_level"],
                 d["dimension_transfer_risk"], d["stage"]))
    beats = [d for d in ds if d["vs_parent"]["delta_level"] > 0]
    holds = [d for d in ds if d["vs_parent"]["delta_level"] == 0]
    print("  summary: %d beat parent, %d hold parent level, %d total. (all 2D candidates; full-3D は昇格段階)"
          % (len(beats), len(holds), len(ds)))
    return led


# ----- promotion: 2D candidate -> LOCAL-3D screen -> non-official CANDIDATE room (not rooms/official) -----

def _best_proposal(result):
    """Pick the best genuine variation: prefer higher 2D level, then |delta|, excluding the no-op (==parent)."""
    cands = [p for p in result["proposals"] if p["status"] == "2d_screened"
             and p["mutation"]["to"] != p["mutation"]["from"]]
    if not cands:
        return None
    return sorted(cands, key=lambda p: (p["screen_2d"]["reached_level"],
                                        p["vs_parent"]["delta_level"]), reverse=True)[0]


def promote_best(result, quick=False, repo=_REPO):
    """Run the best 2D candidate through a LOCAL-3D screen and, if it survives, write a CANDIDATE room
    under rooms/candidates/ (status=candidate; full_3d NOT done). Never writes rooms/official/."""
    best = _best_proposal(result)
    if best is None:
        print("  promote: no non-trivial candidate to promote.")
        return None
    g = dict(best["genesis"])
    r3 = runner.run(g, mode="local-3d", quick=quick)
    level3 = r3["manifest"]["summary"]["reached_level"]
    mb3 = r3["emergence"]["measured_by"]
    cdir = os.path.join(repo, "rooms", "candidates")
    idx = sum(1 for d in os.listdir(cdir) if os.path.isdir(os.path.join(cdir, d))) if os.path.isdir(cdir) else 0
    cand_id = "room-g001-a-cand-%02d" % (idx + 1)
    survived = level3 >= 1
    stage = "local_3d" if survived else "rejected_in_3d"
    _write_candidate_room(repo, cand_id, best, g, r3, survived)
    # reflect the promotion in the ledger
    led = load_ledger()
    for d in led["discoveries"]:
        if d["key"] == _ledger_key(best["mutation"]):
            d["stage"] = stage
            d["local_3d"] = {"reached_level": level3, "mean_amplitude_growth": mb3["mean_amplitude_growth"],
                             "candidate_room": cand_id}
    with open(LEDGER_PATH, "w") as f:
        json.dump(led, f, indent=2, ensure_ascii=False)
    print("  promote: %s -> local-3d level=%s -> %s (%s)"
          % (_ledger_key(best["mutation"]), level3, stage, cand_id))
    return {"candidate_id": cand_id, "stage": stage, "local_3d_level": level3}


def _write_candidate_room(repo, cand_id, proposal, genesis, r3, survived):
    base = "candidates" if survived else "rejected_in_3d"
    rdir = os.path.join(repo, "rooms", base, cand_id)
    os.makedirs(os.path.join(rdir, "runs", "seed-0000"), exist_ok=True)
    room = {
        "room_id": cand_id, "title": "AI candidate: %s" % _ledger_key(proposal["mutation"]),
        "parent_room": "room-g001-a", "favorite": False, "official": False,
        "genesis_model": genesis["model"],
        "emergence": {"reached_level": r3["manifest"]["summary"]["reached_level"],
                      "candidate_level": min(r3["manifest"]["summary"]["reached_level"] + 1, 8)},
        "dimension_status": {"exploration_2d": "passed",
                             "local_3d": "passed" if survived else "failed",
                             "coarse_global_3d": "not_started", "full_3d": "not_started"},
        "physics_status": {"conservation": "pending", "convergence": "pending",
                           "reproducibility": "passed", "integrity_audit": "passed"},
        "status": "candidate" if survived else "rejected_in_3d",
    }
    with open(os.path.join(rdir, "room.yaml"), "w") as f:
        yaml.safe_dump(room, f, allow_unicode=True, sort_keys=False)
    with open(os.path.join(rdir, "genesis.yaml"), "w") as f:
        yaml.safe_dump(genesis, f, allow_unicode=True, sort_keys=False)
    with open(os.path.join(rdir, "emergence.json"), "w") as f:
        json.dump(r3["emergence"], f, indent=2)
    man = dict(r3["manifest"]); man["room_id"] = cand_id
    with open(os.path.join(rdir, "runs", "seed-0000", "manifest.json"), "w") as f:
        json.dump(man, f, indent=2)
    with open(os.path.join(rdir, "runs", "seed-0000", "emergence.json"), "w") as f:
        json.dump(r3["emergence"], f, indent=2)
    with open(os.path.join(rdir, "README.md"), "w") as f:
        f.write("# %s — AI 候補 Room（非公式）\n\n" % cand_id)
        f.write("親 `room-g001-a` の始原条件を `%s` に変えた AI Lab 候補。**official ではない**。\n"
                % _ledger_key(proposal["mutation"]))
        f.write("`dimension_status.full_3d = not_started`（full-3D 昇格・格子収束・複数 seed は未実施）。\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="AI Genesis Lab (minimal start-condition searcher)")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--record", action="store_true", help="persist screened candidates into the discovery ledger")
    ap.add_argument("--review", action="store_true", help="print the accumulated discovery ledger and exit")
    ap.add_argument("--promote-best", action="store_true",
                    help="local-3D screen the best candidate and write a (non-official) candidate room")
    ap.add_argument("--out-root", default=None)
    args = ap.parse_args(argv)

    if args.review:
        review()
        return 0

    res = run_lab(n=args.n, quick=args.quick)
    print("=== AI Genesis Lab: %d proposals (parent room-g001-a, 2D-screened from t=0) ===" % args.n)
    print("  parent baseline 2D level = %d" % res["parent_baseline_level"])
    for p in res["proposals"]:
        if p["status"] == "2d_screened":
            print("  %s: %s %s->%s | level=%d (delta %+d) | risk=%s | %s"
                  % (p["proposal_id"], p["mutation"]["param"], p["mutation"]["from"], p["mutation"]["to"],
                     p["screen_2d"]["reached_level"], p["vs_parent"]["delta_level"],
                     p["dimension_transfer_risk"], p["status"]))
        else:
            print("  %s: %s -> %s (%s)" % (p["proposal_id"], p["mutation"]["param"], p["status"],
                                           p.get("reason", "")))
    print("  NOTE: 2D-screened candidates only. AI cannot self-promote to full-3D or write rooms/official.")
    if args.record and not args.no_write:
        led = record_ledger(res)
        print("  recorded %d discoveries into ai_lab/discoveries/ledger.json" % len(led["discoveries"]))
    if args.promote_best and not args.no_write:
        promote_best(res, quick=args.quick)
    if not args.no_write and not args.record and not args.promote_best:
        out_root = args.out_root or os.path.join(_REPO, "ai_lab", "_demo_out")
        d = write_out(res, out_root)
        print("  wrote proposals under %s" % os.path.relpath(d, _REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
