#!/usr/bin/env python3
"""Multi-backend corroboration: after an Aeterna-Genesis white runs, dispatch the SAME question CONCURRENTLY
to independent reference backends and collect their backing together.

    Aeterna-Genesis (main)
        |-- Genesis-Room- (3D, same model)      -> quantitative backing (observables agree)
        `-- 0-looper      (2D, reduced XY toy)   -> structural  backing (net topo charge ~0, defects coarsen)

Reference repos are used READ-ONLY (cloned to a cache; never modified). Each backend runs in an ISOLATED
SUBPROCESS -- essential, because both reference repos ship a namespace `genesis/` package that would clash
with Aeterna's if imported in-process (an in-process import silently ran the WRONG code -> false backing;
subprocess isolation fixes that AND gives true parallelism). Network-dependent, so this lives in tools/ and
is NOT part of the hermetic test suite (the local-stencil-vs-spectral layer in
genesis/diagnostics/corroborate.py is the CI-side backing). Each backing is labelled by KIND and stays
honest: a reduced XY toy corroborates the STRUCTURE (topology balances, coarsening), not the exact numbers.
"""
import concurrent.futures
import os
import re
import subprocess
import sys

import numpy as np

from genesis.diagnostics.corroborate import observables, agree

_HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.abspath(os.environ.get("CORROB_CACHE", os.path.join(_HERE, "..", ".corrob_refs")))
REPOS = {
    "genesis_room": {"url": "https://github.com/sunpotflower4460-cpu/Genesis-Room-", "dim": 3,
                     "kind": "same_model_quantitative"},
    "zero_looper": {"url": "https://github.com/sunpotflower4460-cpu/0-looper", "dim": 2,
                    "kind": "reduced_mechanism_structural"},
}


def ensure_repo(name):
    """Shallow read-only clone of a reference repo into the cache. Returns path, or None if offline."""
    path = os.path.join(CACHE, name)
    if os.path.isdir(os.path.join(path, ".git")):
        return path
    try:
        os.makedirs(CACHE, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", REPOS[name]["url"], path],
                       check=True, capture_output=True, timeout=180)
        return path
    except Exception as e:  # noqa: BLE001 -- offline is a soft failure
        print("[corroborate] %s unavailable (%s)" % (name, type(e).__name__))
        return None


# ---------- Aeterna side (in-process) ----------

def _plaquette_charge(A):
    """Net topological charge and defect count of a 2D complex field via 2x2 phase-winding plaquettes."""
    th = np.angle(A)

    def wrap(d):
        return (d + np.pi) % (2 * np.pi) - np.pi
    d1 = wrap(np.roll(th, -1, 0) - th)
    d2 = wrap(np.roll(np.roll(th, -1, 0), -1, 1) - np.roll(th, -1, 0))
    d3 = wrap(np.roll(th, -1, 1) - np.roll(np.roll(th, -1, 0), -1, 1))
    d4 = wrap(th - np.roll(th, -1, 1))
    w = np.rint((d1 + d2 + d3 + d4) / (2 * np.pi)).astype(int)
    return int(w.sum()), int(np.count_nonzero(w))


def aeterna_cgl(shape, seed=1, t_final=None):
    """Run Aeterna's cgl_local; return quantitative observables and (2D) structural charge/defect facts."""
    from genesis.models import cgl_local as cg
    tf = t_final if t_final is not None else (40.0 if len(shape) == 2 else 30.0)
    snaps, _ = cg.run(shape, t_final=tf, seed=seed)
    out = {"observables": observables(snaps[-1]["field"])}
    if len(shape) == 2:
        net0, n0 = _plaquette_charge(snaps[len(snaps) // 4]["field"])
        net1, n1 = _plaquette_charge(snaps[-1]["field"])
        out["structural"] = {"net_charge": net1, "defects_early": n0, "defects_late": n1,
                             "coarsens": bool(n1 < n0)}
    return out


# ---------- reference backends (isolated subprocess) ----------

_GR_CODE = (
    "import sys,json; sys.path.insert(0,'.')\n"
    "from genesis import g001_cgl_3d as m; import numpy as np\n"
    "s,_=m.run(tuple({shape}), t_final={tf}, seed={seed}, noise_amplitude=0.01)\n"
    "a=np.abs(s[-1]['field'])\n"
    "print(json.dumps({{'mean_amp':float(a.mean()),'core_frac':float((a<0.5).mean())}}))\n"
)


def backend_genesis_room(shape, seed=1, t_final=30.0):
    path = ensure_repo("genesis_room")
    if path is None:
        return {"status": "unavailable"}
    code = _GR_CODE.format(shape=list(shape), tf=t_final, seed=seed)
    try:
        r = subprocess.run([sys.executable, "-c", code], cwd=path, capture_output=True,
                           text=True, timeout=240, check=True)
        return {"status": "ok", "observables": _last_json(r.stdout)}
    except Exception as e:  # noqa: BLE001
        return {"status": "error:%s" % type(e).__name__}


def parse_vortex_tdgl(text):
    """Parse 0-looper vortex_tdgl quench markdown -> structural facts (net charge, coarsening)."""
    rows = re.findall(r"\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(-?\d+)\s*\|\s*(\d+)\s*\|", text)
    if not rows:
        return None
    first, last = rows[0], rows[-1]
    tot0, tot1 = int(first[4]), int(last[4])
    net1 = int(last[3])
    return {"net_charge": net1, "defects_early": tot0, "defects_late": tot1, "coarsens": bool(tot1 < tot0)}


def backend_zero_looper(L=48, steps=120, seed=1):
    path = ensure_repo("zero_looper")
    if path is None:
        return {"status": "unavailable"}
    try:
        r = subprocess.run([sys.executable, "scripts/vortex_tdgl.py", "--mode", "quench",
                            "--L", str(L), "--steps", str(steps), "--seed", str(seed)],
                           cwd=path, capture_output=True, text=True, timeout=180, check=True)
        s = parse_vortex_tdgl(r.stdout)
        return {"status": "ok", "structural": s} if s else {"status": "parse_failed"}
    except Exception as e:  # noqa: BLE001
        return {"status": "error:%s" % type(e).__name__}


def _last_json(text):
    import json
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    return {}


# ---------- verdicts ----------

def genesis_room_verdict(aeterna_3d, gr, tol=0.15):
    if gr.get("status") != "ok":
        return {"kind": REPOS["genesis_room"]["kind"], "backed": None, "reason": gr.get("status")}
    ok, rel = agree(aeterna_3d["observables"], gr["observables"], tol=tol)
    return {"kind": REPOS["genesis_room"]["kind"], "backed": bool(ok), "rel_diff": rel,
            "aeterna": aeterna_3d["observables"], "reference": gr["observables"]}


def zero_looper_verdict(aeterna_2d, zl):
    if zl.get("status") != "ok":
        return {"kind": REPOS["zero_looper"]["kind"], "backed": None, "reason": zl.get("status")}
    a, z = aeterna_2d["structural"], zl["structural"]
    # structural agreement: BOTH balance net topological charge (~0) AND coarsen (defects decrease)
    both_balanced = abs(a["net_charge"]) <= 2 and z["net_charge"] == 0
    both_coarsen = a["coarsens"] and z["coarsens"]
    return {"kind": REPOS["zero_looper"]["kind"], "backed": bool(both_balanced and both_coarsen),
            "checks": {"both_net_charge_balanced": bool(both_balanced), "both_coarsen": bool(both_coarsen)},
            "aeterna": a, "reference": z}


def corroborate_all(shape2d=(64, 64), shape3d=(24, 24, 24), seed=1, tol=0.15):
    """Run Aeterna (2D+3D), dispatch Genesis-Room (3D) and 0-looper (2D) CONCURRENTLY, return a backing panel
    (2D and 3D corroboration together). Each backend backing is labelled by KIND and stays honest."""
    a3 = aeterna_cgl(shape3d, seed=seed)
    a2 = aeterna_cgl(shape2d, seed=seed)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_gr = ex.submit(backend_genesis_room, shape3d, seed)
        f_zl = ex.submit(backend_zero_looper, shape2d[0], 120, seed)
        gr, zl = f_gr.result(), f_zl.result()
    return {"white": "cgl_local",
            "genesis_room_3d": genesis_room_verdict(a3, gr, tol=tol),
            "zero_looper_2d": zero_looper_verdict(a2, zl)}


if __name__ == "__main__":
    panel = corroborate_all()
    print("=== corroboration panel (cgl_local) ===")
    for backend, v in panel.items():
        if backend == "white":
            continue
        print("%-18s backed=%s kind=%s" % (backend, v.get("backed"), v.get("kind")))
        for k in ("rel_diff", "checks", "reason", "aeterna", "reference"):
            if k in v:
                print("   %-10s %s" % (k, v[k]))
