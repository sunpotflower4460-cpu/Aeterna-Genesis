#!/usr/bin/env python3
"""Cross-repo corroboration (Genesis-Room- auto-backing).

After an Aeterna-Genesis white runs, ALSO run the corresponding Genesis-Room- REFERENCE model and check they
agree on physical observables -- independent-codebase backing for the result. Genesis-Room- is REFERENCE
ONLY: this tool clones it READ-ONLY to a cache dir and never modifies it.

Network-dependent (clones a public repo), so this lives in tools/ and is NOT part of the hermetic test suite.
The hermetic layer (local-stencil vs spectral-FFT) is in genesis/diagnostics/corroborate.py.

Usage:
    python tools/corroborate.py cgl 32          # 2D  32x32
    python tools/corroborate.py cgl 24 24 24     # 3D  24^3
"""
import os
import subprocess
import sys

import numpy as np

from genesis.diagnostics.corroborate import observables, agree

GENESIS_ROOM_URL = "https://github.com/sunpotflower4460-cpu/Genesis-Room-"
DEFAULT_CACHE = os.environ.get("GENESIS_ROOM_CACHE",
                               os.path.join(os.path.dirname(__file__), "..", ".genesis_room_ref"))


def ensure_reference(cache_dir=DEFAULT_CACHE):
    """Clone Genesis-Room- (shallow, read-only) to `cache_dir` if not already present. Returns the path, or
    None if the clone fails (offline) -- corroboration then degrades gracefully."""
    cache_dir = os.path.abspath(cache_dir)
    if os.path.isdir(os.path.join(cache_dir, ".git")):
        return cache_dir
    try:
        subprocess.run(["git", "clone", "--depth", "1", GENESIS_ROOM_URL, cache_dir],
                       check=True, capture_output=True, timeout=120)
        return cache_dir
    except Exception as e:  # noqa: BLE001 -- offline / unavailable is a soft failure
        print("[corroborate] reference unavailable (%s)" % type(e).__name__)
        return None


def corroborate_cgl(shape, t_final=30.0, seed=1, tol=0.15, cache_dir=DEFAULT_CACHE):
    """Run Aeterna's cgl_local AND Genesis-Room-'s g001_cgl_3d from the same params; compare observables.
    Returns a verdict dict (or {'reference': 'unavailable'} offline)."""
    from genesis.models import cgl_local as cg
    snaps, _ = cg.run(shape, t_final=t_final, seed=seed)
    o_aeterna = observables(snaps[-1]["field"])

    ref = ensure_reference(cache_dir)
    if ref is None:
        return {"reference": "unavailable", "aeterna": o_aeterna, "shape": tuple(shape)}
    sys.path.insert(0, ref)
    try:
        import importlib
        gr = importlib.import_module("genesis.g001_cgl_3d")
    except Exception as e:  # noqa: BLE001
        return {"reference": "import_failed:%s" % type(e).__name__, "aeterna": o_aeterna}
    finally:
        pass
    # match noise amplitude & dt convention (both default 0.01, stable_dt)
    gsnaps, _ = gr.run(tuple(shape), t_final=t_final, seed=seed, noise_amplitude=0.01)
    o_ref = observables(gsnaps[-1]["field"])
    ok, rel = agree(o_aeterna, o_ref, tol=tol)
    return {"corroborated": ok, "tol": tol, "rel_diff": rel, "aeterna": o_aeterna, "genesis_room": o_ref,
            "reference_repo": GENESIS_ROOM_URL, "shape": tuple(shape)}


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "cgl":
        shp = tuple(int(x) for x in sys.argv[2:])
        v = corroborate_cgl(shp)
        print("corroborate_cgl", shp, "->")
        for k, val in v.items():
            print("  %-14s %s" % (k, val))
    else:
        print(__doc__)
        sys.exit(1)
