"""P2 treasure audit, part 1: index and classify every candidate Room (read-only on rooms/).

For each ``rooms/candidates/<room>/`` this writes one JSONL row (start conditions, measured level, checksum,
disk size) and a class:

    keep-full   hand-made / human-referenced rooms, one representative per (condition cell, dimension, level),
                and statistical outliers inside their cell -- these keep their full field data
    distill     other rooms that reached Level 2 -- a small uint8 keyframe asset is kept (--keyframes)
    index-only  the rest (Level 1) -- the JSONL row is the record; raw data stays recoverable from git

It never modifies or deletes anything under rooms/. ``--determinism N`` re-runs N rooms from t=0 with the
recorded start conditions and compares ``final_field_sha256``: if they match, the raw field files are
regenerable and "index-only" loses nothing that cannot be recomputed.

    python tools/audit/rooms_index.py                       # index + classify -> audit/candidates.*
    python tools/audit/rooms_index.py --determinism 60      # + re-run check   -> audit/determinism.json
    python tools/audit/rooms_index.py --keyframes           # + audit/candidates_keyframes.npz
"""
from __future__ import annotations

import argparse
import base64
import collections
import glob
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
_CAND = _REPO / "rooms" / "candidates"
_OUT = _REPO / "audit"
# Human-curated text where a reference to a room means somebody chose to cite it.
_HUMAN_REF_GLOBS = ("docs/**/*.md", "experiments/**/*.md", "experiments/**/*.yaml", "rooms/official/**/*.yaml",
                    "rooms/official/**/*.md", "*.md")
_ROOM_ID = re.compile(r"room-[A-Za-z0-9_.-]+")


def _load(path: Path):
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) if path.suffix in (".yaml", ".yml") else json.load(fh)


def _dir_bytes(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def human_references() -> collections.Counter:
    refs: collections.Counter = collections.Counter()
    for pattern in _HUMAN_REF_GLOBS:
        for f in glob.glob(str(_REPO / pattern), recursive=True):
            if "INVENTORY_" in f or "/audit/" in f:
                continue
            refs.update(set(_ROOM_ID.findall(Path(f).read_text(encoding="utf-8", errors="replace"))))
    return refs


def room_row(room: Path) -> dict:
    g = _load(room / "genesis.yaml") or {}
    ry = _load(room / "room.yaml") or {}
    em = _load(room / "emergence.json") or {}
    ist = g.get("initial_state") or {}
    quench = (g.get("protocol") or {}).get("quench") or {}
    runs = sorted(room.glob("runs/*/manifest.json"))
    man = _load(runs[0]) if runs else {}
    summary = (man or {}).get("summary") or {}
    measured = em.get("measured_by") or {}
    return {
        "room_id": room.name,
        "model": g.get("model") or ry.get("genesis_model"),
        "dimension": g.get("dimension"),
        "mode": (man or {}).get("mode"),
        "seed": g.get("seed"),
        "noise_amplitude": ist.get("noise_amplitude"),
        "quench_duration": quench.get("duration"),
        "correlation_length": ist.get("correlation_length"),
        "initial_type": ist.get("type"),
        "reached_level": em.get("reached_level", (ry.get("emergence") or {}).get("reached_level")),
        "candidate_level": em.get("candidate_level", (ry.get("emergence") or {}).get("candidate_level")),
        "defect_count": measured.get("defect_count"),
        "persistent_defects": measured.get("persistent_defects"),
        "structure_factor_prominence": measured.get("structure_factor_prominence"),
        "conservation_drift": summary.get("conservation_drift"),
        "final_mean_amplitude": summary.get("final_mean_amplitude"),
        "final_field_sha256": ((man or {}).get("checksum") or {}).get("final_field_sha256"),
        "run_dir": str(runs[0].parent.relative_to(_REPO)) if runs else None,
        "bytes": _dir_bytes(room),
        "auto_dream": room.name.startswith("room-auto-dream-"),
    }


def cell_key(r: dict) -> str:
    return f"{r['model']}|noise={r['noise_amplitude']}|quench={r['quench_duration']}|corr={r['correlation_length']}|ic={r['initial_type']}"


def classify(rows: list[dict], refs: collections.Counter) -> None:
    groups: dict[tuple, list[dict]] = collections.defaultdict(list)
    for r in rows:
        r["cell"] = cell_key(r)
        groups[(r["cell"], r["dimension"])].append(r)
    reps: set[str] = set()
    outliers: dict[str, str] = {}
    for (_, _dim), members in groups.items():
        by_level: dict = collections.defaultdict(list)
        for r in members:
            by_level[r["reached_level"]].append(r)
        for lvl_members in by_level.values():  # one deterministic representative per (cell, dim, level)
            reps.add(min(lvl_members, key=lambda r: (r["seed"] or 0, r["room_id"]))["room_id"])
        for key in ("conservation_drift", "defect_count"):
            vals = [float(r[key]) for r in members if isinstance(r.get(key), (int, float))]
            if len(vals) < 8:
                continue
            mu, sd = statistics.fmean(vals), statistics.pstdev(vals)
            if sd <= 0:
                continue
            for r in members:
                v = r.get(key)
                if isinstance(v, (int, float)) and abs(float(v) - mu) > 3 * sd:
                    outliers.setdefault(r["room_id"], f"{key} z={(float(v) - mu) / sd:+.1f} in cell")
    for r in rows:
        why = []
        if not r["auto_dream"]:
            why.append("hand-made or non-Dream room")
        if refs.get(r["room_id"]):
            why.append(f"cited in human-curated docs ({refs[r['room_id']]} files)")
        if r["room_id"] in reps:
            why.append("representative of its (condition cell, dimension, level)")
        if r["room_id"] in outliers:
            why.append("outlier: " + outliers[r["room_id"]])
        if why:
            r["class"], r["reason"] = "keep-full", "; ".join(why)
        elif r["reached_level"] == 2:
            r["class"], r["reason"] = "distill", "Level 2 (defects present) but a duplicate seed of an indexed cell"
        else:
            r["class"], r["reason"] = "index-only", f"Level {r['reached_level']}; duplicate seed of an indexed cell"


def determinism(rows: list[dict], n: int) -> dict:
    from genesis.runners.recorded_runner import run_recorded

    auto = [r for r in rows if r["auto_dream"] and r["final_field_sha256"] and r["mode"]]
    by_cell: dict = collections.defaultdict(list)
    for r in auto:
        by_cell[(r["cell"], r["dimension"])].append(r)
    picked: list[dict] = []
    keys = sorted(by_cell)
    i = 0
    while len(picked) < min(n, len(auto)):  # round-robin over cells so every cell is sampled
        members = sorted(by_cell[keys[i % len(keys)]], key=lambda r: r["room_id"])
        k = i // len(keys)
        if k < len(members):
            picked.append(members[k])
        i += 1
        if i > n * len(keys):
            break
    results = []
    for r in picked:
        genesis = _load(_CAND / r["room_id"] / "genesis.yaml")
        mode = {"local_3d": "local-3d", "2d_screen": "2d-screen"}.get(r["mode"], r["mode"])
        out = run_recorded(genesis, mode=mode, quick=True)
        sha = out["manifest"]["checksum"]["final_field_sha256"]
        results.append({"room_id": r["room_id"], "mode": mode, "recorded": r["final_field_sha256"], "rerun": sha,
                        "match": sha == r["final_field_sha256"]})
        print(f"  {'OK ' if results[-1]['match'] else 'MISMATCH'} {r['room_id']}", flush=True)
    matched = sum(x["match"] for x in results)
    return {"sampled": len(results), "matched": matched, "cells_covered": len({(r['cell'], r['dimension']) for r in picked}),
            "numpy": np.__version__, "python": sys.version.split()[0], "results": results}


def keyframes(rows: list[dict], frames: int = 4, edge: int = 24) -> tuple[np.ndarray, list[str]]:
    """uint8 [N, frames, edge, edge, 2 lenses (phase, density)] for distill + keep-full rooms (3D: mid z-slice)."""
    from scipy import ndimage

    ids, stack = [], []
    for r in rows:
        if r["class"] not in ("distill", "keep-full") or not r["run_dir"]:
            continue
        fj = _REPO / r["run_dir"] / "field.json"
        if not fj.is_file():
            continue
        d = json.load(fj.open())
        grid, nf = d["grid"], d["nframes"]
        pick = np.linspace(0, nf - 1, frames).round().astype(int)
        lenses = []
        for lens in ("phase", "density"):
            arr = np.frombuffer(base64.b64decode(d["lenses"][lens]["data_b64"]), np.uint8).reshape(nf, *grid)
            if len(grid) == 3:
                arr = arr[:, grid[0] // 2]
            arr = arr[pick].astype(float)
            zoom = (1, edge / arr.shape[1], edge / arr.shape[2])
            lenses.append(np.clip(ndimage.zoom(arr, zoom, order=0 if lens == "phase" else 1), 0, 255).astype(np.uint8))
        ids.append(r["room_id"])
        stack.append(np.stack(lenses, axis=-1))
    return (np.stack(stack) if stack else np.zeros((0, frames, edge, edge, 2), np.uint8)), ids


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--determinism", type=int, default=0, help="re-run this many rooms from t=0 and compare checksums")
    ap.add_argument("--keyframes", action="store_true", help="write audit/candidates_keyframes.npz")
    a = ap.parse_args()
    _OUT.mkdir(exist_ok=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_REPO, capture_output=True, text=True).stdout.strip()

    rows = [room_row(p) for p in sorted(_CAND.iterdir()) if p.is_dir()]
    refs = human_references()
    classify(rows, refs)
    with (_OUT / "candidates.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    cells: dict = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        cells[r["cell"]][f"d{r['dimension']}-L{r['reached_level']}"] += 1
    by_class = collections.Counter(r["class"] for r in rows)
    bytes_by_class = collections.Counter()
    for r in rows:
        bytes_by_class[r["class"]] += r["bytes"]
    summary = {
        "source_commit": head,
        "rooms": len(rows),
        "models": dict(collections.Counter(r["model"] for r in rows)),
        "dimensions": dict(collections.Counter(str(r["dimension"]) for r in rows)),
        "reached_level": dict(collections.Counter(str(r["reached_level"]) for r in rows)),
        "candidate_level_rule": "candidate_level = reached_level + 1 (genesis/runners/*runner.py) -- a target label, not a measurement",
        "distinct_condition_cells": len(cells),
        "cells": {k: dict(v) for k, v in sorted(cells.items())},
        "class_counts": dict(by_class),
        "class_bytes": dict(bytes_by_class),
        "ignored_by_room_runner": "run_recorded() applies only initial_state.noise_amplitude and protocol.quench; "
                                  "Dream knobs (diffusion_ratio, drive_strength, IC family, correlation_length) are not "
                                  "part of these rooms",
    }
    if a.determinism:
        summary["determinism"] = determinism(rows, a.determinism)
        (_OUT / "determinism.json").write_text(json.dumps(summary["determinism"], indent=2), encoding="utf-8")
    if a.keyframes:
        arr, ids = keyframes(rows)
        np.savez_compressed(_OUT / "candidates_keyframes.npz", frames=arr, room_ids=np.array(ids),
                            lenses=np.array(["phase", "density"]))
        summary["keyframes"] = {"rooms": len(ids), "shape": list(arr.shape),
                                "bytes": os.path.getsize(_OUT / "candidates_keyframes.npz")}
    (_OUT / "candidates_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("cells",)}, indent=2, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()
