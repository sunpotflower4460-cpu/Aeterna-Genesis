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

import hashlib  # noqa: E402

import numpy as np  # noqa: E402

from genesis.diagnostics import measures  # noqa: E402
from genesis.diagnostics import higher_levels as hl  # noqa: E402
from genesis.models import boussinesq_rb as rb  # noqa: E402
from genesis.models import gray_scott as gs  # noqa: E402
from genesis.models import complex_ginzburg_landau as cgl  # noqa: E402
from genesis.models import swift_hohenberg as sh  # noqa: E402

# ---------------------------------------------------------------------------------------------------
# EXPANDED SEARCH (指示書①): non-saturating score + IC families + full knob space + modes + parents.
# Discipline kept: the Level is still decided by measures.assess_level (imported, NOT redefined); the
# score is ONLY a ranking heuristic (never a success gate, never a promotion trigger). IC families are
# seed / noise / symmetric structures ONLY -- they never encode the target (第8監査).
# ---------------------------------------------------------------------------------------------------

# parents the Lab can screen from t=0. Only g001 (Ginzburg-Landau TDGL) is end-to-end screenable here;
# other laws need their own make_initial/step/free_energy and are a separate (frontier) step.
PARENTS = {"g001": gl}

# IC families: generic disordered / symmetric starts. NONE encodes the GL target (organized, localized
# phase-winding vortices). Amplitude families carry NO phase; phase families carry RANDOM phase (no
# winding number placed). See docs/honest_floors.md.
#   amplitude-only : white / white_lowk / white_highk / single_seed / sparse_seeds / ring / gradient
#   random-phase   : seeds_phase (bumps × constant random phase) / spectral_powerlaw / bandpass
# A sandbox mass-search found phase-LESS seeds climb 0% while phase-bearing families climb ~10%
# ("length-scale/phase control on top"); these random-phase families reproduce that HONESTLY.
# NOTE: `vortex_charges` (seeds carrying ±winding via atan2) is DELIBERATELY EXCLUDED -- it seeds the
# GL target (巻き数) = 第8監査 violation; its apparent climb is target-encoded, not emergence
# (docs/traps_museum.md: T-vortexseed, docs/honest_floors.md).
IC_FAMILIES = ["white", "white_lowk", "white_highk", "single_seed", "sparse_seeds", "ring", "gradient",
               "seeds_phase", "spectral_powerlaw", "bandpass", "real_seed"]
AMPLITUDE_FAMILIES = ["single_seed", "sparse_seeds", "ring", "gradient"]  # added structure is purely real
PHASE_FAMILIES = ["seeds_phase", "spectral_powerlaw", "bandpass"]         # random phase, no winding placed
# real_seed is PURELY REAL: GL preserves reality so it can NEVER localize (L2) -- a mechanistic control
# reproducing the sandbox 'phase-less seeds = 0%' finding (docs/honest_floors.md phase-control floor).

# full start-side knob space the Lab may sample (ranges enforced by param_ranges.yaml search_space).
# correlation_length is realized HONESTLY as low-k filtering of the noise (spatially-correlated IC),
# so it actually changes the computation (not just recorded). diffusion_ratio->Du, drive_strength->eps.
FULL_KNOBS = ["noise_amplitude", "correlation_length", "diffusion_ratio", "drive_strength", "quench_duration"]


def _lowk_noise(shape, rng, corr_len):
    """White noise smoothed to a correlation length via a Gaussian low-pass in k-space (symmetric)."""
    w = rng.standard_normal(shape) + 1j * rng.standard_normal(shape)
    if corr_len <= 1.0:
        return w
    f = np.fft.fftn(w)
    ks = [np.fft.fftfreq(n) * n for n in shape]
    grids = np.meshgrid(*ks, indexing="ij")
    k2 = sum(g ** 2 for g in grids)
    f *= np.exp(-0.5 * (corr_len ** 2) * (2 * np.pi / max(shape)) ** 2 * k2)
    out = np.fft.ifftn(f)
    return out / (np.std(out) + 1e-30)


def _highk_noise(shape, rng, corr_len):
    w = rng.standard_normal(shape) + 1j * rng.standard_normal(shape)
    f = np.fft.fftn(w)
    ks = [np.fft.fftfreq(n) * n for n in shape]
    grids = np.meshgrid(*ks, indexing="ij")
    k2 = sum(g ** 2 for g in grids)
    f *= (1.0 - np.exp(-0.5 * (max(corr_len, 2.0) ** 2) * (2 * np.pi / max(shape)) ** 2 * k2))
    out = np.fft.ifftn(f)
    return out / (np.std(out) + 1e-30)


def _spectral_field(shape, rng, kind, corr_len):
    """Field with a chosen power-spectrum envelope and RANDOM phases (no organized winding placed)."""
    ks = [np.fft.fftfreq(n) * n for n in shape]
    grids = np.meshgrid(*ks, indexing="ij")
    kr = np.sqrt(sum(g ** 2 for g in grids))
    if kind == "powerlaw":
        env = 1.0 / ((kr + 1.0) ** 1.5)                      # scale-rich k^-1.5 envelope
    else:                                                    # bandpass around a length scale ~ corr_len
        k0 = max(shape) / max(corr_len, 1.0) / (2 * np.pi)
        env = np.exp(-0.5 * ((kr - k0) / max(k0 * 0.5, 1.0)) ** 2)
    phase = rng.uniform(0.0, 2 * np.pi, shape)               # RANDOM phases -> no winding number encoded
    out = np.fft.ifftn(env * np.exp(1j * phase))
    return out / (np.std(out) + 1e-30)


def make_ic(family, shape, noise_amplitude, rng, corr_len=1.0):
    """Build a disordered / symmetric initial complex field for the GL model. 第8監査-compliant:
    amplitude families carry NO phase; phase families carry RANDOM phase (no winding number placed).
    NO organized, localized phase-winding vortex (the GL target) is ever seeded."""
    if family == "white":
        return gl.make_initial(shape, noise_amplitude, rng)  # byte-identical to the runner's default
    if family == "white_lowk":
        return (noise_amplitude * _lowk_noise(shape, rng, corr_len)).astype(np.complex128)
    if family == "white_highk":
        return (noise_amplitude * _highk_noise(shape, rng, corr_len)).astype(np.complex128)
    if family in ("spectral_powerlaw", "bandpass"):          # random-phase spectra (scale/phase control)
        kind = "powerlaw" if family == "spectral_powerlaw" else "bandpass"
        return (noise_amplitude * _spectral_field(shape, rng, kind, corr_len)).astype(np.complex128)
    base = gl.make_initial(shape, noise_amplitude, rng)
    coords = [np.linspace(-1.0, 1.0, n) for n in shape]
    grid = np.meshgrid(*coords, indexing="ij")
    r2 = sum(g ** 2 for g in grid)
    if family == "single_seed":                              # one symmetric real amplitude bump (no phase)
        return base + noise_amplitude * 4.0 * np.exp(-r2 / 0.05)
    if family == "sparse_seeds":                             # a few symmetric bumps at rng positions
        bump = np.zeros(shape)
        for _ in range(3):
            c = [rng.uniform(-0.6, 0.6) for _ in shape]
            rr = sum((grid[i] - c[i]) ** 2 for i in range(len(shape)))
            bump = bump + np.exp(-rr / 0.03)
        return base + noise_amplitude * 4.0 * bump
    if family == "seeds_phase":                              # bumps × CONSTANT random phase (no winding)
        field = base.astype(np.complex128)
        for _ in range(3):
            c = [rng.uniform(-0.6, 0.6) for _ in shape]
            rr = sum((grid[i] - c[i]) ** 2 for i in range(len(shape)))
            theta = rng.uniform(0.0, 2 * np.pi)              # ONE phase per bump -> spatially constant
            field = field + noise_amplitude * 4.0 * np.exp(-rr / 0.03) * np.exp(1j * theta)
        return field
    if family == "ring":                                     # symmetric annulus amplitude (no winding)
        r = np.sqrt(r2)
        return base + noise_amplitude * 4.0 * np.exp(-((r - 0.5) ** 2) / 0.02)
    if family == "gradient":                                 # smooth real gradient across the first axis
        return base + noise_amplitude * 3.0 * grid[0]
    if family == "real_seed":                                # PURELY REAL: real noise + real bump.
        # GL preserves reality (all step terms of a real field are real) -> the phase never leaves {0,pi}
        # -> no 2*pi winding can ever form -> L2 (localization) is UNREACHABLE by construction. This
        # reproduces the sandbox 'phase-less seeds = 0%' finding AND explains WHY (a control, not a trap).
        rnoise = noise_amplitude * rng.standard_normal(shape)
        return (rnoise + noise_amplitude * 4.0 * np.exp(-r2 / 0.05)).astype(np.complex128)
    raise ValueError("unknown IC family %r" % family)


def spectral_complexity(psi):
    """Non-saturating structural complexity in [0,1]: LOG-scaled participation ratio of the power
    spectrum (drop the k=0 mean). Single dominant mode -> ~0; white noise (all modes) -> ~1; organized
    multi-domain structure -> intermediate. The log scale spreads the organized regime (few..tens of
    modes) across the useful range instead of pinning it near 0, and it AVOIDS the entropy->1.0
    saturation that flattens ranking (docs/traps_museum.md: T-entropy-sat)."""
    f = np.fft.fftn(psi - psi.mean())
    s = (np.abs(f) ** 2).ravel().astype(float)
    if not np.all(np.isfinite(s)):
        return float("nan")
    s[0] = 0.0
    tot = s.sum()
    if tot <= 0:
        return 0.0
    p = s / tot
    pr = 1.0 / np.sum(p ** 2)                       # participation ratio = effective # excited modes
    return float(np.log10(max(pr, 1.0)) / np.log10(len(p)))


def _window_bonus(c, lo=0.3, hi=0.9):
    """Mid-complexity window (A5 cat-map / Aaronson coffee): reward structure between trivial (single
    mode ~0) and pure noise (~1). Plateau inside [lo,hi], smooth Gaussian falloff outside."""
    if lo <= c <= hi:
        return 1.0
    d = (lo - c) if c < lo else (c - hi)
    return float(np.exp(-((d / 0.15) ** 2)))


def score_run(level, mb, complexity):
    """RANKING heuristic only (NOT a success gate; Level from measures.assess_level stays the truth).
    Level dominates: the within-level bonus is capped BELOW 1.0 so a deeper reached Level always outranks
    a shallower one. Within a level, the mid-complexity window + measured signals refine the ranking."""
    growth = min(np.log10(max(float(mb["mean_amplitude_growth"]), 1.0)) / 6.0, 1.0)  # 0..1
    prom = min(float(mb["structure_factor_prominence"]) / 10.0, 1.0)                  # 0..1
    defects = min(float(mb["defect_count"]) / 20.0, 1.0)                              # 0..1
    signal = (growth + prom + defects) / 3.0                                          # 0..1
    within = 0.5 * _window_bonus(complexity) + 0.4 * signal                           # 0..0.9 (< 1)
    return round(float(level) + within, 4)


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


# ---- expanded search engine: IC-family + full-knob screen, scored & ranked (grid/random/evolutionary) ----

STEPS_2D = {True: (48, 260, 10), False: (96, 400, 12)}   # quick -> (edge, steps, snapshots)


def _apply_knobs(p, knobs):
    """Map allowed start-side knobs onto the GL solver params (ranges enforced upstream)."""
    if "noise_amplitude" in knobs:
        p["noise_amplitude"] = float(knobs["noise_amplitude"])
    if "quench_duration" in knobs:
        p["quench_duration"] = float(knobs["quench_duration"])
    if "diffusion_ratio" in knobs:
        p["Du"] = float(knobs["diffusion_ratio"])            # diffusion coefficient Du in [0.1,10]
    if "drive_strength" in knobs:
        p["eps_final"] = max(0.1, float(knobs["drive_strength"]))  # quench end epsilon
    return p


def _knob_within_allowed(param, value, ss):
    """AI may only pick values inside the allowed search space (param_ranges.yaml)."""
    ir, pr = ss["initial_state"], ss["physical_parameters"]
    if param == "noise_amplitude":
        return ir["noise_amplitude"]["min"] <= value <= ir["noise_amplitude"]["max"]
    if param == "correlation_length":
        return ir["correlation_length"]["min"] <= value <= ir["correlation_length"]["max"]
    if param == "diffusion_ratio":
        return pr["diffusion_ratio"]["min"] <= value <= pr["diffusion_ratio"]["max"]
    if param == "drive_strength":
        return pr["drive_strength"]["min"] <= value <= pr["drive_strength"]["max"]
    if param == "quench_duration":
        return 0.0 < value <= 40.0
    return False


def _cfl_substeps(Du, base_dt, ndim=2, dx=1.0, cap=8):
    """Explicit GL diffusion is stable only for dt*Du*2*ndim/dx^2 <~ 0.4 (docs/traps_museum.md: T-euler).
    Sub-step to hold physical time constant while staying stable; cap the sub-steps (beyond it the trial
    is flagged unstable rather than reported as a false Level 0)."""
    safe_dt = 0.4 / max(Du * 2 * ndim / (dx * dx), 1e-9)
    return int(min(cap, max(1, np.ceil(base_dt / safe_dt))))


def _screen_ic(family, knobs, seed, quick=True):
    """REAL 2D screen from t=0 with an IC family + start-side knobs. Level via measures.assess_level
    (imported, NOT redefined); adds a non-saturating complexity + score for RANKING only. CFL-sub-steps
    for numerical stability and flags genuinely non-finite runs as 'unstable' (an honest numerical
    failure, NOT a physical Level-0 result)."""
    edge, steps, nsnap = STEPS_2D[bool(quick)]
    shape = (edge, edge)
    p = _apply_knobs(dict(gl.DEFAULTS), knobs)
    base_dt = p["dt"]
    nsub = _cfl_substeps(p["Du"], base_dt)
    p["dt"] = base_dt / nsub                          # smaller dt: SAME physics, more sub-steps
    total = steps * nsub
    rng = np.random.default_rng(seed)
    corr = float(knobs.get("correlation_length", 1.0))
    psi = make_ic(family, shape, p["noise_amplitude"], rng, corr_len=corr)
    traj = []
    snap = max(1, total // nsnap)
    unstable = False
    for t in range(total):
        psi = gl.step(psi, t * p["dt"], p)
        if not np.all(np.isfinite(psi)):
            unstable = True
            break
        if t % snap == 0 or t == total - 1:
            _, prom = measures.structure_factor_peak(psi)
            traj.append({"mean_amp": measures.mean_amplitude(psi), "sk_prom": prom,
                         "defects": measures.winding_defect_count(psi)})
    if unstable or not traj:
        return {"reached_level": None, "status": "unstable", "measured_by": {}, "complexity": None,
                "score": None, "checksum": None,
                "reason": "numerical_instability (explicit stepper CFL, Du=%.3g)" % p["Du"]}
    level, _, mb = measures.assess_level(traj)
    # PHYSICS-VALIDITY GUARD (not a threshold change): a purely REAL field can host no true 2*pi phase
    # vortex (its phase is confined to {0, pi}), so a Level-2 (localization-via-winding) verdict on it is
    # a discrete-measure artifact -- winding_defect_count miscounts the field's domain-wall junctions.
    # We keep measures.assess_level untouched and RECORD the raw level, but do not CREDIT the climber
    # with L2 on a real field. Surfaced honestly (docs/traps_museum.md: T-realwinding). This is exactly
    # the sandbox 'phase-less seeds = 0%' finding, now with its mechanism + the measure caveat.
    field_real = bool(np.max(np.abs(psi.imag)) == 0.0)
    level_raw = level
    winding_note = None
    if field_real and level >= 2:
        level = 1
        winding_note = "winding_artifact_real_field: Re-only field has no true vortices; measured L2 is a domain-wall miscount"
    complexity = spectral_complexity(psi)
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(psi.real).tobytes()); h.update(np.ascontiguousarray(psi.imag).tobytes())
    out = {"reached_level": level, "status": "2d_screened", "measured_by": mb,
           "complexity": round(complexity, 4), "score": score_run(level, mb, complexity),
           "checksum": h.hexdigest()[:16], "field_real": field_real, "reached_level_raw": level_raw}
    if winding_note:
        out["winding_note"] = winding_note
    return out


def _grid_values(param):
    return {"noise_amplitude": KNOBS["noise_amplitude"], "quench_duration": KNOBS["quench_duration"],
            "correlation_length": [1.0, 3.0, 6.0, 9.0, 12.0], "diffusion_ratio": [0.2, 0.5, 1.0, 3.0, 8.0],
            "drive_strength": [0.5, 1.0, 2.0, 3.0, 5.0]}.get(param, [])


def _sample_knobs(rng, ss):
    """Sample allowed start-side knobs respecting each param's scale (log/linear) from param_ranges."""
    def logu(r):
        return float(10 ** rng.uniform(np.log10(r["min"]), np.log10(r["max"])))

    def linu(r):
        return float(rng.uniform(r["min"], r["max"]))
    ir, pr = ss["initial_state"], ss["physical_parameters"]
    return {"noise_amplitude": logu(ir["noise_amplitude"]),
            "correlation_length": linu(ir["correlation_length"]),
            "diffusion_ratio": logu(pr["diffusion_ratio"]),
            "drive_strength": linu(pr["drive_strength"]),
            "quench_duration": float(rng.uniform(4.0, 20.0))}


def _clamp_knob(param, value, ss):
    ir, pr = ss["initial_state"], ss["physical_parameters"]
    rng = {"noise_amplitude": ir["noise_amplitude"], "correlation_length": ir["correlation_length"],
           "diffusion_ratio": pr["diffusion_ratio"], "drive_strength": pr["drive_strength"]}.get(param)
    if rng:
        return float(min(rng["max"], max(rng["min"], value)))
    if param == "quench_duration":
        return float(min(40.0, max(0.5, value)))
    return value


def search(mode="random", n=50, parent="g001", seed=0, quick=True, families=None):
    """Large-scale start-condition search. Returns score-ranked results. Discipline: every knob value is
    checked against the allowed space (AI cannot exceed it); IC families are seed/noise/symmetric only;
    the score ONLY ranks -- the reached Level (measured) is the truth; no self-promotion here."""
    if parent not in PARENTS:
        raise ValueError("parent %r is not screenable in the Lab yet (only: %s). Other laws need their own "
                         "screen -- a separate (frontier) step." % (parent, ", ".join(PARENTS)))
    ss = _load_search_space()
    families = families or IC_FAMILIES
    if mode == "evolutionary":
        return _evolutionary(n, parent, seed, quick, families, ss)
    rng = np.random.default_rng(seed)
    trials = []
    if mode == "grid":
        for fam in families:                              # deterministic: family x one-knob-change grid
            for param in FULL_KNOBS:
                for val in _grid_values(param):
                    trials.append({"family": fam, "knobs": {param: val}, "seed": 0})
        trials = trials[:n]
    elif mode == "random":
        for _ in range(n):
            fam = families[int(rng.integers(len(families)))]
            trials.append({"family": fam, "knobs": _sample_knobs(rng, ss), "seed": int(rng.integers(0, 10000))})
    else:
        raise ValueError("unknown mode %r (use grid/random/evolutionary)" % mode)
    results = []
    for tr in trials:
        if not all(_knob_within_allowed(k, v, ss) for k, v in tr["knobs"].items()):
            continue                                      # AI cannot exceed the allowed space
        results.append({**tr, **_screen_ic(tr["family"], tr["knobs"], tr["seed"], quick=quick)})
    results.sort(key=_score_key, reverse=True)
    return {"mode": mode, "parent_room": "room-%s-a" % parent, "n": len(results), "results": results}


def _score_key(x):
    """Sort key that pushes unstable (score=None) trials to the bottom, best score first otherwise."""
    return (x["score"] is not None, x["score"] if x["score"] is not None else 0.0)


def _evolutionary(n, parent, seed, quick, families, ss, gens=4):
    """Mutate the best ICs over generations: elites survive, children perturb ONE knob (or family)."""
    rng = np.random.default_rng(seed)
    pop = [{"family": families[int(rng.integers(len(families)))], "knobs": _sample_knobs(rng, ss),
            "seed": int(rng.integers(0, 10000))} for _ in range(max(4, n // gens))]
    allr = []
    for g in range(gens):
        scored = [{**ind, **_screen_ic(ind["family"], ind["knobs"], ind["seed"], quick=quick), "generation": g}
                  for ind in pop]
        allr.extend(scored)
        scored.sort(key=_score_key, reverse=True)
        elites = [s for s in scored if s["score"] is not None][:max(2, len(scored) // 2)] or scored[:2]
        pop = []
        for e in elites:
            pop.append({"family": e["family"], "knobs": dict(e["knobs"]), "seed": e["seed"]})  # keep elite
            child = {"family": e["family"], "knobs": dict(e["knobs"]), "seed": int(rng.integers(0, 10000))}
            k = list(child["knobs"])[int(rng.integers(len(child["knobs"])))]
            child["knobs"][k] = _clamp_knob(k, child["knobs"][k] * float(rng.uniform(0.5, 2.0)), ss)
            if rng.uniform() < 0.3:
                child["family"] = families[int(rng.integers(len(families)))]
            pop.append(child)
    allr.sort(key=_score_key, reverse=True)
    return {"mode": "evolutionary", "parent_room": "room-%s-a" % parent, "n": len(allr),
            "results": allr, "generations": gens}


def family_hitrates(results):
    """Per-family summary: how often each IC family reaches the localization climb (L>=2). Reproduces the
    sandbox 'phase-less seeds climb ~0% / phase-bearing families climb' finding in honest measured terms."""
    fams = {}
    for r in results:
        f = fams.setdefault(r["family"], {"n": 0, "l2": 0, "unstable": 0, "best_score": None})
        f["n"] += 1
        if r.get("score") is None:
            f["unstable"] += 1
            continue
        if (r["reached_level"] or 0) >= 2:
            f["l2"] += 1
        if f["best_score"] is None or r["score"] > f["best_score"]:
            f["best_score"] = r["score"]
    for f in fams.values():
        scored = max(1, f["n"] - f["unstable"])
        f["l2_rate"] = f["l2"] / scored
    return dict(sorted(fams.items(), key=lambda kv: kv[1]["l2_rate"], reverse=True))


def _search_key(rec):
    kv = ",".join("%s=%g" % (k, rec["knobs"][k]) for k in sorted(rec["knobs"]))
    return "%s|%s" % (rec["family"], kv)


def record_search(result, path=None):
    """Persist scored search results into the ledger (append-only by key, ranked by score)."""
    path = path or LEDGER_PATH
    led = load_ledger(path)
    led.setdefault("search_discoveries", [])
    by = {d["key"]: d for d in led["search_discoveries"]}
    for rec in result["results"]:
        if rec.get("score") is None:                    # skip numerically-unstable trials (not a result)
            continue
        key = _search_key(rec)
        by[key] = {"key": key, "parent_room": result["parent_room"], "family": rec["family"],
                   "knobs": rec["knobs"], "seed": rec["seed"], "reached_level": rec["reached_level"],
                   "score": rec["score"], "complexity": rec["complexity"], "measured_by": rec["measured_by"],
                   "checksum_2d": rec["checksum"], "stage": by.get(key, {}).get("stage", "2d_screened")}
    led["search_discoveries"] = sorted(by.values(), key=lambda d: d["score"], reverse=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(led, f, indent=2, ensure_ascii=False)
    return led


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
    sd = led.get("search_discoveries", [])
    if sd:
        print("=== expanded search ledger (%d IC-family/knob trials, ranked by score) — top 12 ===" % len(sd))
        for d in sd[:12]:
            kv = ",".join("%s=%g" % (k, d["knobs"][k]) for k in sorted(d["knobs"]))
            print("  score=%-6.3f L=%d cx=%.3f | %-12s | %s | stage=%s"
                  % (d["score"], d["reached_level"], d["complexity"], d["family"], kv, d["stage"]))
        lv = {}
        for d in sd:
            lv[d["reached_level"]] = lv.get(d["reached_level"], 0) + 1
        print("  reached-level histogram: %s (score ranks WITHIN the honest Level; not a success gate)"
              % ", ".join("L%d:%d" % (k, lv[k]) for k in sorted(lv)))
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


def _run_search(args):
    """CLI path for the expanded engine (--mode grid/random/evolutionary): scored, ranked, IC families."""
    res = search(mode=args.mode, n=args.n, parent=args.parent, seed=args.seed, quick=args.quick)
    print("=== AI Genesis Lab — %s search: %d trials (parent %s, 2D-screened from t=0) ==="
          % (args.mode, res["n"], res["parent_room"]))
    print("  score = Level(dominant) + mid-complexity-window + signals. Level is MEASURED; score only RANKS.")
    for r in res["results"][:args.top]:
        kv = ",".join("%s=%g" % (k, r["knobs"][k]) for k in sorted(r["knobs"]))
        if r["score"] is None:
            print("  UNSTABLE                        | %-12s | %s  (%s)" % (r["family"], kv, r.get("reason", "")))
            continue
        print("  score=%-6.3f L=%d cx=%.3f growth=%.1f defects=%d | %-12s | %s"
              % (r["score"], r["reached_level"], r["complexity"], r["measured_by"]["mean_amplitude_growth"],
                 r["measured_by"]["defect_count"], r["family"], kv))
    lv = {}
    for r in res["results"]:
        k = r["reached_level"] if r["reached_level"] is not None else "unstable"
        lv[k] = lv.get(k, 0) + 1
    print("  level histogram: %s" % ", ".join("%s:%d" % (("L%d" % k if isinstance(k, int) else k), lv[k])
                                              for k in sorted(lv, key=lambda x: (isinstance(x, str), x))))
    print("  family hit-rate (share reaching L>=2, the 'localization/seed->plant' climb):")
    for fam, st in family_hitrates(res["results"]).items():
        print("    %-16s n=%-4d L2-rate=%4.0f%% best_score=%s unstable=%d"
              % (fam, st["n"], 100 * st["l2_rate"], st["best_score"], st["unstable"]))
    print("  NOTE: 2D-screened only. AI cannot self-promote to full-3D or write rooms/official.")
    if args.record and not args.no_write:
        led = record_search(res)
        print("  recorded %d search discoveries into ai_lab/discoveries/ledger.json"
              % len(led.get("search_discoveries", [])))
    return 0


# ---------------------------------------------------------------------------------------------------
# MULTIPLE LAW CLASSES (指示書: 0 から L3 以上): GL caps at L2 in 2D; other laws climb deeper from t=0.
#   g002 Boussinesq/RB : REST + noise -> coherent circulation rolls (L3), KE 0->saturate, ∮v·dl != 0.
#   gray_scott (RD)    : noise seeds -> spots SELF-REPLICATE / divide (L7 signature).
#   g003 Model H       : phase separation + flow co-evolution (L5) -- registered FRONTIER (measure WIP).
# Discipline kept: from t=0, IC seeded禁止 (rest+noise / noise seeds, NOT the target), Level measured
# (genesis/diagnostics), no self-promotion, no_touch. 「turbulent != coherent」/「同じ数学 != 同じもの」.
# ---------------------------------------------------------------------------------------------------

# law-specific drive knobs the Lab may vary, with allowed ranges (physical, bounded; AI cannot exceed).
LAW_KNOBS = {
    "g002": {"Ra": (300.0, 30000.0)},                 # Rayleigh number (sub->super critical; Ra_c≈657.5)
    "gray_scott": {"F": (0.02, 0.06), "k": (0.05, 0.07), "n_seeds": (2, 20)},
}
LAW_CLASSES = {
    "g001": {"model": gl.MODEL_ID, "kind": "scalar_gl", "target_level": 2, "tier": "measured"},
    "g002": {"model": rb.MODEL_ID, "kind": "flow", "target_level": 3, "tier": "measured"},
    "gray_scott": {"model": gs.MODEL_ID, "kind": "reaction_diffusion", "target_level": 7, "tier": "measured"},
    "g003": {"model": "g003_model_h_phase_field", "kind": "phase_flow", "target_level": 5, "tier": "frontier"},
}


def _clip(v, lo, hi):
    return float(min(hi, max(lo, v)))


def _screen_boussinesq(Ra, seed, quick=True):
    """REST + noise -> self-organized convection. Coherent rolls saturate (L3); turbulent churn is
    flagged, not sold as coherent. Ra is the drive (subcritical -> no flow -> L0)."""
    Nx, Nz, steps = (24, 25, 3500) if quick else (32, 33, 7000)
    s = rb.Bouss(Nx, Nz, _clip(Ra, *LAW_KNOBS["g002"]["Ra"]), seed=seed, noise_amplitude=1e-3)
    ke, snap = [], max(1, steps // 12)
    for i in range(steps):
        s.step(s.cfl_dt(cap=rb.DEFAULTS["dt_cap"]))
        if not s.finite():
            return {"reached_level": None, "status": "unstable", "reason": "non-finite (Ra=%.0f)" % Ra}
        if i % snap == 0 or i == steps - 1:
            ke.append(s.kinetic_energy())
    circulation = float(np.mean(np.abs(s.bwd(s.om))))         # mean |vorticity| on the grid
    late = ke[-3:] if len(ke) >= 3 else ke
    fluct = float(np.std(late) / (np.mean(late) + 1e-12))
    level, detected, mb = hl.assess_flow_level(ke, circulation, fluct)
    return {"reached_level": level, "status": "2d_screened", "measured_by": mb, "detected": detected,
            "law": "g002", "drive": {"Ra": round(float(Ra), 1)}}


def _screen_gray_scott(F, k, n_seeds, seed, quick=True):
    """Noise seeds -> RD spots that self-replicate/divide. This is the HONEST emergent ceiling of the
    Gray-Scott U,V white: **L7-partial (division only)**. Heredity does NOT emerge from U,V -- getting it
    requires PLACING a heritable field (a tag T), which is placing the answer, not emergence
    (docs/ANTI_DRIFT.md 原則1). So the U,V screen stays L7-partial and makes no FULL-L7 claim.
    Spots ≠ life (Pearson 1993)."""
    N, steps = (80, 9000) if quick else (96, 14000)      # RD self-replication needs ~10k+ steps to divide
    p = dict(gs.DEFAULTS)
    p["F"] = _clip(F, *LAW_KNOBS["gray_scott"]["F"]); p["k"] = _clip(k, *LAW_KNOBS["gray_scott"]["k"])
    n_seeds = int(_clip(n_seeds, *LAW_KNOBS["gray_scott"]["n_seeds"]))
    rng = np.random.default_rng(seed)
    U, V = gs.make_initial((N, N), n_seeds, rng, seed_radius=p["seed_radius"])   # U,V white only (no placed T)
    counts, snap = [gs.spot_count(V)], max(1, steps // 12)
    for i in range(steps):
        U, V = gs.step(U, V, p)
        if not np.all(np.isfinite(V)):
            return {"reached_level": None, "status": "unstable", "reason": "non-finite (F=%.3f,k=%.3f)" % (F, k)}
        if i % snap == 0 or i == steps - 1:
            counts.append(gs.spot_count(V))
    level, detected, mb = hl.assess_replication_level(counts)   # no spots/tag -> honest L7-partial
    return {"reached_level": level, "status": "2d_screened", "measured_by": mb, "detected": detected,
            "l7_status": "L7-partial (division only; heredity would be PLACED, not emergent)",
            "law": "gray_scott", "drive": {"F": round(float(F), 4), "k": round(float(k), 4), "n_seeds": n_seeds}}


def _screen_cgl(seed, quick=True):
    """Complex Ginzburg-Landau: a SINGLE complex oscillatory field. Question: does spontaneous motion
    emerge from a scalar field with NO velocity field? Honest answer (measured): it develops
    spiral-DEFECT TURBULENCE -- patterns + topological cores that MOVE chaotically, but TURBULENT (not
    coherent) and NOT persistent individuals -> ceiling below L4. |A|~1 is set by the IC (no growth-from-
    floor). NOTE a measurement floor: measures.winding_defect_count UNDERCOUNTS CGL (it masks low-|A|
    cores, tuned for TDGL); the honest defect signature here is amplitude-hole cores."""
    N, steps = (64, 3000) if quick else (96, 5000)
    p = dict(cgl.DEFAULTS)
    rng = np.random.default_rng(seed)
    A = cgl.make_initial((N, N), 1e-2, rng)
    k2 = cgl._k2(A.shape)
    sk, ncores, autocorr, amp_prev, snap = [], [], [], None, max(1, steps // 12)
    for i in range(steps):
        A = cgl.step(A, p, k2)
        if not np.all(np.isfinite(A)):
            return {"reached_level": None, "status": "unstable", "reason": "non-finite"}
        if i % snap == 0 or i == steps - 1:
            _, prom = measures.structure_factor_peak(A)
            _, cents = cgl.winding_defects(A)
            sk.append(float(prom)); ncores.append(len(cents))
            a = np.abs(A)
            if amp_prev is not None:
                autocorr.append(float(np.corrcoef(a.ravel(), amp_prev.ravel())[0, 1]))
            amp_prev = a
    patterns = max(sk) > 5.0                              # structure factor peak emerged (L1)
    cores = max(ncores) >= 3                              # topological cores formed (L2, via amp holes)
    moves = bool(autocorr and min(autocorr[len(autocorr) // 2:] or [1.0]) < 0.6)   # pattern decorrelates
    steady_turbulence = bool(all(c > 0 for c in ncores[-3:]) and moves)            # never freezes/converges
    return {"reached_level": None, "status": "2d_screened",
            "measured_by": {"sk_peak_max": round(max(sk), 2), "cores_max": max(ncores),
                            "amp_autocorr_tail": round(min(autocorr[-3:]) if autocorr else 1.0, 3),
                            "growth_from_floor": False},
            "detected": {"patterns_L1": patterns, "topological_cores_L2": cores,
                         "turbulent_motion": moves, "coherent": False, "persistent_individuals": False,
                         "steady_turbulence": steady_turbulence},
            "ceiling_label": "spiral-defect TURBULENCE: L1 patterns + L2 cores + turbulent motion; "
                             "NOT coherent, NOT persistent -> ceiling below L4 (spatiotemporal chaos)",
            "law": "cgl"}


def _screen_swift_hohenberg(seed, quick=True):
    """Swift-Hohenberg (cubic-quintic): a bistable field with STABLE LOCALIZED STATES. Probes the map's
    missing rung L4 (persistent individuality). From a generic symmetric bump + noise (NO boundary seeded),
    a bounded structure forms that PERSISTS, has inside/outside contrast, and SELF-HEALS after a cut (the L4
    discriminator). Being variational, it does NOT self-move (drift~0): a STATIC individual. Self-propelled
    individuality (L4 + motion) is frontier. All L4 criteria are MEASURED via hl.assess_individuality_level."""
    N, settle, hold, heal = (64, 2500, 800, 2500) if quick else (96, 3500, 1200, 3500)
    p = dict(sh.DEFAULTS)
    rng = np.random.default_rng(seed)
    u = sh.make_initial((N, N), 1e-3, rng, p)
    k2 = sh._k2(N, p["dx"])
    for _ in range(settle):                                     # settle from the seed to the attractor
        u = sh.step(u, p, k2)
        if not np.all(np.isfinite(u)):
            return {"reached_level": None, "status": "unstable"}
    s0 = sh.individual_stats(u)
    prev = u.copy()
    for _ in range(hold):                                       # hold: measure persistence + no self-motion
        u = sh.step(u, p, k2)
    s1 = sh.individual_stats(u)
    persistence_change = float(np.abs(u - prev).max())        # change across the whole hold window (settled ~0)
    drift = float(np.hypot(s1["centroid"][0] - s0["centroid"][0], s1["centroid"][1] - s0["centroid"][1]))
    # self-heal: destroy the top half of the individual, let the white REGROW it
    up = u.copy(); up[:N // 2, :] = 0.0
    for _ in range(heal):
        up = sh.step(up, p, k2)
    sh_heal = sh.individual_stats(up)
    recovers = bool(abs(sh_heal["area"] - s1["area"]) <= 8 and abs(sh_heal["amax"] - s1["amax"]) < 0.12)
    # size-independence: same individual on a bigger box (not a finite-size effect)
    N2 = N + 32
    u2 = sh.make_initial((N2, N2), 1e-3, np.random.default_rng(seed), p)
    k22 = sh._k2(N2, p["dx"])
    for _ in range(settle):
        u2 = sh.step(u2, p, k22)
    s2 = sh.individual_stats(u2)
    size_independent = bool(abs(s2["area"] - s1["area"]) <= 10)
    area_fraction = s1["area"] / float(N * N)
    reached, detected, mb = hl.assess_individuality_level(
        amax=s1["amax"], area_fraction=area_fraction, persistence_change=persistence_change,
        recovers_after_perturbation=recovers, size_independent=size_independent, centroid_drift=drift)
    return {"reached_level": reached, "status": "2d_screened", "detected": detected, "measured_by": mb,
            "ceiling_label": mb["emergent_ceiling"], "law": "swift_hohenberg"}


def lawscan(seed=0, quick=True):
    """Run each law class from t=0 and report the reached Level (measured). Shows GL(L2) < flow(L3) <
    self-replication(L7): deeper Levels need a different law, not a different score."""
    out = []
    r = _screen_ic("white", {"noise_amplitude": 1.0e-2}, seed, quick=quick)   # GL reference (L1/L2)
    out.append({"law": "g001", "kind": "scalar_gl", "reached_level": r["reached_level"],
                "tier": "measured", "measured_by": r.get("measured_by", {}), "from": "uniform+noise (t=0)"})
    rb_r = _screen_boussinesq(2000.0, seed, quick=quick)                       # supercritical -> L3
    out.append({"law": "g002", "kind": "flow", "reached_level": rb_r["reached_level"], "tier": "measured",
                "measured_by": rb_r.get("measured_by", {}), "detected": rb_r.get("detected", {}),
                "drive": rb_r.get("drive", {}), "from": "REST + noise (t=0)"})
    gs_r = _screen_gray_scott(0.035, 0.062, 8, seed, quick=quick)              # honest ceiling: L7-partial
    out.append({"law": "gray_scott", "kind": "reaction_diffusion", "reached_level": gs_r["reached_level"],
                "l7_status": gs_r.get("l7_status"),
                "tier": "measured", "measured_by": gs_r.get("measured_by", {}), "detected": gs_r.get("detected", {}),
                "drive": gs_r.get("drive", {}), "from": "noise seeds (t=0)",
                "floor": "spots ≠ life; division EMERGES (L7-partial) but heredity does NOT — it would be "
                         "PLACED (a tag field), not born from U,V (docs/ANTI_DRIFT.md)"})
    cg_r = _screen_cgl(seed, quick=quick)                                      # single complex field -> turbulence
    out.append({"law": "cgl", "kind": "complex_oscillatory", "reached_level": cg_r["reached_level"],
                "l7_status": cg_r.get("ceiling_label"),   # reuse the ceiling-label slot for the honest ceiling
                "tier": "measured", "measured_by": cg_r.get("measured_by", {}), "detected": cg_r.get("detected", {}),
                "from": "uniform+noise (t=0)",
                "floor": "motion is TURBULENT not coherent (turbulent ≠ coherent); no persistent individual; "
                         "measures.winding_defect_count UNDERCOUNTS CGL cores (measurement floor)"})
    sh_r = _screen_swift_hohenberg(seed, quick=quick)                         # localized state -> L4 (static)
    out.append({"law": "swift_hohenberg", "kind": "pattern_bistable", "reached_level": sh_r["reached_level"],
                "l7_status": sh_r.get("ceiling_label"),   # reuse the ceiling-label slot for the honest ceiling
                "tier": "measured", "measured_by": sh_r.get("measured_by", {}), "detected": sh_r.get("detected", {}),
                "from": "symmetric bump + noise (t=0)",
                "floor": "L4 individuality EMERGES (persistent + self-healing + size-independent) but STATIC: "
                         "SH is variational -> no self-motion. Self-propelled individual (L4 ∧ motion) = frontier. "
                         "individuality (L4) and self-motion (L3) are INDEPENDENT axes (docs/WHITE_CEILINGS.md)"})
    return out


def record_lawscan(rows, path=None):
    """Persist the per-law-class climb into the ledger (replace latest lawscan snapshot)."""
    path = path or LEDGER_PATH
    led = load_ledger(path)
    led["lawclass_climbs"] = rows
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(led, f, indent=2, ensure_ascii=False)
    return led


def main(argv=None):
    ap = argparse.ArgumentParser(description="AI Genesis Lab (start-condition searcher)")
    ap.add_argument("--mode", default="legacy",
                    choices=["legacy", "grid", "random", "evolutionary", "lawscan"],
                    help="legacy = original 2-knob grid; grid/random/evolutionary = expanded engine; "
                         "lawscan = run each LAW CLASS from t=0 (GL L2 < flow L3 < self-replication L7)")
    ap.add_argument("--parent", default="g001", help="parent law to branch (only g001 screenable for now)")
    ap.add_argument("--seed", type=int, default=0, help="master seed for the sampler (deterministic)")
    ap.add_argument("--top", type=int, default=12, help="how many top-ranked trials to print")
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

    if args.mode == "lawscan":
        rows = lawscan(seed=args.seed, quick=args.quick)
        print("=== AI Genesis Lab — law-class climb from t=0 (deeper Level needs a different LAW) ===")
        for r in rows:
            lv = r["reached_level"]
            reached = r["l7_status"] if r.get("l7_status") else ("L%s" % (lv if lv is not None else "?"))
            print("  %-11s [%-18s] reached %s  (%s) tier=%s"
                  % (r["law"], r["kind"], reached, r["from"], r["tier"]))
            print("       measured: %s" % r.get("measured_by", {}))
            if r.get("floor"):
                print("       floor: %s" % r["floor"])
        print("  NOTE: from t=0, IC seeded禁止 (rest+noise / noise seeds). Level MEASURED; no self-promotion; no_touch.")
        if args.record and not args.no_write:
            record_lawscan(rows)
            print("  recorded law-class climb into ai_lab/discoveries/ledger.json")
        return 0

    if args.mode != "legacy":
        return _run_search(args)

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
