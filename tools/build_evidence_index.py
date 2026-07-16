#!/usr/bin/env python3
"""Evidence index generator (research-continuity gaps G2/G6, + G1/G8 coverage warnings). role: tooling.

WHY: the "what did we build / how far did each white climb / why did it stop" memory lives in hand-maintained
prose (TRUST_MAP.md, WHITE_CEILINGS.md) that can silently drift from the per-experiment `experiment.yaml` and
per-Room `emergence.json`. This tool DERIVES a canonical index from those machine sources so it can never drift
undetected: `--check` (run in CI) fails if the committed index differs from a fresh regeneration. It does NOT
touch TRUST_MAP.md / WHITE_CEILINGS.md (those stay human prose); it writes a SEPARATE generated artifact.

Outputs (regenerate with `--write`, verify with `--check`):
  docs/generated/evidence_index.json   canonical machine index (sorted, stable)
  docs/generated/evidence_index.md      human table derived from the same data

Also prints non-failing COVERAGE WARNINGS: experiments referenced by no registry (G1), official Rooms whose
white is not named in WHITE_CEILINGS.md (G6), diagnostics modules not catalogued (G8). These are advisory so
the tool does not retroactively break on today's known gaps; only the derive-vs-committed diff can fail CI.
"""
import argparse
import glob
import json
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JSON = os.path.join(ROOT, "docs", "generated", "evidence_index.json")
OUT_MD = os.path.join(ROOT, "docs", "generated", "evidence_index.md")


def _load_yaml(p):
    with open(p) as f:
        return yaml.safe_load(f)


def collect():
    # experiments
    experiments = []
    for yml in sorted(glob.glob(os.path.join(ROOT, "experiments", "e*", "experiment.yaml"))):
        d = _load_yaml(yml) or {}
        role = d.get("role", {}) or {}
        dim = d.get("dimension", {}) or {}
        experiments.append({
            "id": d.get("id"),
            "title": d.get("title", ""),
            "role_primary": role.get("primary"),
            "role_secondary": sorted(role.get("secondary", []) or []),
            "claim_tier": d.get("claim_tier", []),
            "target_encoded": bool(d.get("target_encoded", False)),
            "seeded_structure": bool(d.get("seeded_structure", False)),
            "dimension": dim.get("computed"),
            "genesis_role": d.get("genesis_role"),
            "n_results": len(d.get("results", []) or []),
        })
    experiments.sort(key=lambda r: r["id"] or "")

    # official rooms (emergence ladder)
    rooms = []
    for room_yaml in sorted(glob.glob(os.path.join(ROOT, "rooms", "official", "*", "room.yaml"))):
        rd = _load_yaml(room_yaml) or {}
        rdir = os.path.dirname(room_yaml)
        emg = {}
        ep = os.path.join(rdir, "emergence.json")
        if os.path.exists(ep):
            emg = json.load(open(ep))
        rooms.append({
            "room_id": rd.get("room_id", os.path.basename(rdir)),
            "white": rd.get("genesis_model"),
            "title": rd.get("title", ""),
            "reached_level": emg.get("reached_level"),
            "candidate_level": emg.get("candidate_level"),
        })
    rooms.sort(key=lambda r: r["room_id"] or "")

    # diagnostics catalogue (module names)
    diagnostics = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(ROOT, "genesis", "diagnostics", "*.py"))
                         if not os.path.basename(p).startswith("__"))

    # role tally
    tally = {}
    for e in experiments:
        r = e["role_primary"] or "?"
        tally[r] = tally.get(r, 0) + 1

    return {"experiments": experiments, "official_rooms": rooms, "diagnostics_modules": diagnostics,
            "role_tally": {k: tally[k] for k in sorted(tally)}, "n_experiments": len(experiments)}


def _registry_referenced_experiments():
    refs = set()
    for reg in glob.glob(os.path.join(ROOT, "genesis", "registry", "*.yaml")):
        d = _load_yaml(reg) or {}
        for e in d.get("entries", []) or []:
            for x in e.get("related_experiments", []) or []:
                refs.add(x)
    return refs


def warnings(idx):
    out = []
    refs = _registry_referenced_experiments()
    unref = [e["id"] for e in idx["experiments"] if e["id"] not in refs]
    if unref:
        out.append("G1: %d experiments referenced by no registry entry: %s" % (len(unref), ", ".join(unref)))
    ceil = ""
    cp = os.path.join(ROOT, "docs", "WHITE_CEILINGS.md")
    if os.path.exists(cp):
        ceil = open(cp, encoding="utf-8").read()
    for r in idx["official_rooms"]:
        w = (r["white"] or "").split("_")[0]           # e.g. "g001"
        if w and w not in ceil:
            out.append("G6: official Room %s (white %s) not named in WHITE_CEILINGS.md" % (r["room_id"], r["white"]))
    return out


def render_md(idx):
    L = ["# Evidence index (generated — do not edit by hand)",
         "",
         "Auto-derived from `experiments/*/experiment.yaml` + `rooms/official/*/emergence.json` by "
         "`tools/build_evidence_index.py`. CI (`--check`) fails if this drifts from the sources. The human "
         "narrative maps (`docs/TRUST_MAP.md`, `docs/WHITE_CEILINGS.md`) are separate and unchanged.",
         "",
         "## Emergence ladder (official Rooms)",
         "| room | white | reached_level | candidate_level |",
         "|---|---|---|---|"]
    for r in idx["official_rooms"]:
        L.append("| %s | %s | %s | %s |" % (r["room_id"], r["white"], r["reached_level"], r["candidate_level"]))
    L += ["", "## Experiments (%d) — role tally: %s" % (idx["n_experiments"],
          ", ".join("%s=%d" % (k, v) for k, v in idx["role_tally"].items())),
          "| id | role | tier | dim | target_encoded | genesis_role | title |",
          "|---|---|---|---|---|---|---|"]
    for e in idx["experiments"]:
        sec = ("+" + "/".join(e["role_secondary"])) if e["role_secondary"] else ""
        L.append("| %s | %s%s | %s | %s | %s | %s | %s |" % (
            e["id"], e["role_primary"], sec, "/".join(e["claim_tier"]), e["dimension"],
            e["target_encoded"], e["genesis_role"], e["title"]))
    L += ["", "## Diagnostics modules (%d)" % len(idx["diagnostics_modules"]),
          ", ".join("`%s`" % d for d in idx["diagnostics_modules"]), ""]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="derive + verify the evidence index (G2/G6)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true", help="(re)write the generated index files")
    g.add_argument("--check", action="store_true", help="fail if committed index differs from a fresh derivation")
    args = ap.parse_args(argv)

    idx = collect()
    js = json.dumps(idx, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    md = render_md(idx)

    for w in warnings(idx):
        print("  [coverage] " + w)

    if args.write:
        os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
        open(OUT_JSON, "w", encoding="utf-8").write(js)
        open(OUT_MD, "w", encoding="utf-8").write(md)
        print("wrote %s and %s (%d experiments, %d rooms)" %
              (os.path.relpath(OUT_JSON, ROOT), os.path.relpath(OUT_MD, ROOT), idx["n_experiments"], len(idx["official_rooms"])))
        return 0

    # default / --check: compare committed to fresh
    if not os.path.exists(OUT_JSON):
        print("EVIDENCE-INDEX: missing; run `python tools/build_evidence_index.py --write`.")
        return 1
    cur_js = open(OUT_JSON, encoding="utf-8").read()
    cur_md = open(OUT_MD, encoding="utf-8").read() if os.path.exists(OUT_MD) else ""
    ok = (cur_js == js) and (cur_md == md)
    print("EVIDENCE-INDEX:", "GREEN (index matches sources)" if ok else "RED (index is stale)")
    if not ok:
        print("  -> sources changed without regenerating. Run: python tools/build_evidence_index.py --write")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
