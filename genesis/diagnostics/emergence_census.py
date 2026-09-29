"""Count what happened in a universe built from a spec (genesis/models/sb_universe.py) WITHOUT naming it first.

A measuring instrument only: it does not know what should form, and it does not look for walls, strings or particles
by name. Everything is counted in the same general way for every spec:

    energy_parts      where the energy sits: kinetic, gradient, potential, electric, magnetic
    valleys / labels  every site's field value is rolled downhill in V (pointwise, a measurement) and the end points
                      are grouped by chaining (single linkage): a discrete set of valleys gives separate groups, a
                      continuous valley one connected group. The number of flat directions at the valley (Hessian)
                      tells whether it is a set of points or a manifold. A charged field's phase is not physical, so
                      with light (e > 0) the groups are formed in gauge-invariant coordinates.
    domains           a site is IN a valley when it lies closer to it than half the way to the next valley (else it
                      is "between": still on the top, or inside a wall or a core); connected regions of sites in the
                      same group, their sizes; bonds between
                      different groups (where regions meet, by pair of groups: the "kinds" of meeting), and
                      plaquettes whose corners belong to three or more groups (where three or more regions meet)
    windings          for every complex field, plaquettes around which its phase winds (gauge-invariant with light);
                      with several fields, how many windings are shared by all of them at the same place
    lumps             connected regions of high energy density that do not span the box, with their content,
                      size, charges and windings inside; tracked through time with genesis/diagnostics/lump_tracker
    kinds             lumps and domains grouped by their rounded features; within a kind, how different the members
                      are (shape descriptors): are any two exactly the same?
    Spectrum          ω–k power of gauge-invariant local fields (time series of axis modes): how many frequency
                      branches there are at small k, and their gaps (masses). The FFT is used only here, to measure.

What the census does not decide: whether something is "a particle", "alive", "the same thing". It reports numbers.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

from genesis.diagnostics import lump_tracker as lt
from genesis.models import abelian_higgs_nd as ah
from genesis.models import sb_universe as sb


# ------------------------------------------------------------------------------------------ energy
def energy_parts(spec, st) -> dict[str, float]:
    r, c, th = st["r"], st["c"], st["th"]
    a = sb.scale_factor(spec, st["tau"])
    out = {"kinetic": 0.0, "gradient": 0.0, "potential": 0.0, "electric": 0.0, "magnetic": 0.0}
    out["potential"] = float((a ** 4 * sb.potential(spec, r / a, c / a)).sum())
    for i in range(spec["real"]):
        f = r[i]
        out["kinetic"] += float(0.5 * (st["pr"][i] ** 2).sum())
        out["gradient"] += float(0.5 * spec["c_real"][i] ** 2 * sum(((ah._sh(f, x) - f) ** 2).sum()
                                                                    for x in range(f.ndim)))
    for k in range(spec["complex"]):
        f = c[k]
        out["kinetic"] += float((np.abs(st["pc"][k]) ** 2).sum())
        ph = [np.exp(-1j * th[x]) if spec["e"] else 1.0 for x in range(f.ndim)]
        out["gradient"] += float(spec["c_complex"][k] ** 2 * sum((np.abs(ph[x] * ah._sh(f, x) - f) ** 2).sum()
                                                                 for x in range(f.ndim)))
    if spec["e"]:
        out["electric"] = float(0.5 * spec["e"] ** 2 * (st["E"] ** 2).sum())
        out["magnetic"] = float(sum((1.0 - np.cos(ah.plaquette(th, i, j))).sum()
                                    for i, j in ah.planes(th.shape[0])) / spec["e"] ** 2)
    tot = sum(out.values())
    out["total"] = tot
    return out


# ------------------------------------------------------------------------------------------ valleys
def _canon(spec, r, c):
    """Canonical coordinates x (R + 2N, …) with s = ½|x|²; φ_a = (q1 + i q2)/√2."""
    return np.concatenate([r, np.sqrt(2.0) * c.real, np.sqrt(2.0) * c.imag], axis=0)


def _uncanon(spec, x):
    R, N = spec["real"], spec["complex"]
    return x[:R], (x[R:R + N] + 1j * x[R + N:]) / np.sqrt(2.0)


def invariants(spec, r, c) -> np.ndarray:
    """Coordinates for grouping valleys: the fields themselves without light; with light the gauge-invariant ones
    (real fields, |φ_a|², and Re/Im φ_a* φ_b for a < b)."""
    if not spec["e"]:
        return _canon(spec, r, c)
    N = spec["complex"]
    rows = list(r) + [np.abs(c[a]) ** 2 for a in range(N)]
    for a in range(N):
        for b in range(a + 1, N):
            z = np.conj(c[a]) * c[b]
            rows += [z.real, z.imag]
    return np.stack(rows)


def roll_down(spec, r, c, iters: int = 4000, tol: float = 1e-6):
    """Every point rolls downhill in V until it stops (pointwise gradient descent in canonical coordinates, each point
    with its own step: longer while V keeps falling, a step that would raise V is undone and shortened)."""
    x = _canon(spec, r, c).astype(float)
    eta0 = 0.5 / max(sb.curvature_bound(spec), 1e-9)
    eta = np.full(x.shape[1], eta0)
    live = np.arange(x.shape[1])

    def grad_V(xs):
        rr, cc = _uncanon(spec, xs)
        gr, gc = sb.potential_grad(spec, rr, cc)
        return np.concatenate([gr, np.sqrt(2.0) * gc.real, np.sqrt(2.0) * gc.imag], axis=0), sb.potential(spec, rr, cc)

    g, V = grad_V(x)
    for _ in range(iters):
        xs = x[:, live] - eta[live] * g[:, live]
        gn, Vn = grad_V(xs)
        ok = Vn <= V[live]
        idx = live[ok]
        moved = np.abs(xs[:, ok] - x[:, idx]).max(0) if idx.size else np.zeros(0)
        x[:, idx], g[:, idx], V[idx] = xs[:, ok], gn[:, ok], Vn[ok]
        eta[idx] = np.minimum(eta[idx] * 1.5, 1e3 * eta0)
        eta[live[~ok]] *= 0.5
        done = np.zeros(live.size, bool)
        done[ok] = moved < tol
        done |= eta[live] < 1e-6 * eta0
        live = live[~done]
        if live.size == 0:
            break
    return _uncanon(spec, x)


def _hessian_eigs(spec, x0: np.ndarray, h: float = 1e-4) -> np.ndarray:
    """Eigenvalues of the Hessian of V at one point of field space (canonical coordinates)."""
    n = x0.size

    def V(x):
        rr, cc = _uncanon(spec, x[:, None])
        return float(sb.potential(spec, rr, cc)[0])

    Hm = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            ei, ej = np.eye(n)[i] * h, np.eye(n)[j] * h
            Hm[i, j] = Hm[j, i] = (V(x0 + ei + ej) - V(x0 + ei - ej) - V(x0 - ei + ej) + V(x0 - ei - ej)) / (4 * h * h)
    return np.linalg.eigvalsh(Hm)


def _flat_directions(ev: np.ndarray) -> int:
    return int((np.abs(ev) < 1e-3 * max(np.abs(ev).max(), 1e-12)).sum())


def _along_the_valley(spec, xa: np.ndarray, xb: np.ndarray, Vv: float, vmax: float, rng) -> bool:
    """Can one go from valley point xa to xb without leaving the valley? Points on a path between them (straight,
    or bent sideways) are rolled down; connected when every rolled point stays at the valley's V and the rolled
    points follow each other without a jump."""
    s = np.linspace(0.0, 1.0, 65)[:, None]
    paths = [xa + s * (xb - xa)]
    for _ in range(3):
        w = rng.standard_normal(xa.size)
        d = xb - xa
        w -= w @ d / max(d @ d, 1e-30) * d
        w *= 0.5 * np.linalg.norm(d) / max(np.linalg.norm(w), 1e-30)
        paths.append(xa + s * (xb - xa) + (1.0 - np.abs(2 * s - 1)) * w)
    for P in paths:
        rr, cc = roll_down(spec, *_uncanon(spec, P.T))
        X = _canon(spec, rr, cc)
        Vp = sb.potential(spec, rr, cc)
        if (Vp <= Vv + 1e-6 * (1 + abs(Vv))).all() and (np.linalg.norm(np.diff(X, axis=1), axis=0) < 0.25 * vmax).all():
            return True
    return False


def _chain(points: np.ndarray, tol: float) -> np.ndarray:
    """Single-linkage groups of points (rows) at distance ≤ tol."""
    tree = cKDTree(points)
    parent = np.arange(len(points))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i, j in tree.query_pairs(tol):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
    roots = np.array([find(i) for i in range(len(points))])
    _, lab = np.unique(roots, return_inverse=True)
    return lab


def label_sites(spec, st, max_points: int = 20000) -> tuple[np.ndarray, list[dict[str, Any]]]:
    """Each site -> the group of the valley its field value rolls into. Returns (labels (grid), groups)."""
    a = sb.scale_factor(spec, st["tau"])
    shape = (st["r"] if spec["real"] else st["c"]).shape[1:]
    size = int(np.prod(shape))
    r = (st["r"] / a).reshape(spec["real"], size)
    c = (st["c"] / a).reshape(spec["complex"], size)
    rr, cc = roll_down(spec, r, c)
    moved = np.linalg.norm(_canon(spec, r, c) - _canon(spec, rr, cc), axis=0)
    inv = invariants(spec, rr, cc).T                                  # (sites, dims)
    vmax = max([t.get("v", 1.0) for t in spec["terms"]] + [1.0])
    q = np.round(inv / (1e-3 * vmax)).astype(np.int64)
    uq, back = np.unique(q, axis=0, return_inverse=True)
    back = back.ravel()
    reps = uq.astype(float) * 1e-3 * vmax
    if len(reps) > max_points:                                        # a continuous valley densely sampled
        keep = np.random.default_rng(0).choice(len(reps), max_points, replace=False)
        lab_k = _chain(reps[keep], 0.05 * vmax)
        _, nn = cKDTree(reps[keep]).query(reps)
        lab_u = lab_k[nn]
    else:
        lab_u = _chain(reps, 0.05 * vmax)
    labels = lab_u[back]
    xe = _canon(spec, rr, cc)
    G = int(labels.max()) + 1
    first = np.array([np.flatnonzero(labels == g)[0] for g in range(G)])
    reps_x = xe[:, first].T
    Vg = sb.potential(spec, rr[:, first], cc[:, first])
    eigs = [_hessian_eigs(spec, reps_x[g]) for g in range(G)]
    scale = max(float(np.abs(np.concatenate(eigs)).max()), 1e-12)
    top = np.array([ev.min() < -1e-3 * scale for ev in eigs])      # stopped on a top or a saddle, not in a valley
    flat = np.array([_flat_directions(ev) for ev in eigs])
    # a continuous valley sampled with gaps falls into several groups: join groups that are connected along it
    parent = np.arange(G)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    cand = [g for g in range(G) if flat[g] > 0 and not top[g]]
    if len(cand) > 1:
        rng = np.random.default_rng(0)
        tree = cKDTree(reps_x[cand])
        _, nb = tree.query(reps_x[cand], k=min(4, len(cand)))
        for i, g in enumerate(cand):
            for j in np.atleast_1d(nb[i])[1:]:
                h = cand[int(j)]
                if find(g) == find(h) or abs(Vg[g] - Vg[h]) > 1e-6 * (1 + abs(Vg[g])):
                    continue
                if _along_the_valley(spec, reps_x[g], reps_x[h], float(Vg[g]), vmax, rng):
                    parent[find(g)] = find(h)
    roots = np.array([find(g) for g in range(G)])
    keep = sorted({int(roots[g]) for g in range(G) if not top[g]})
    new_id = {k: i for i, k in enumerate(keep)}
    gmap = np.array([new_id.get(int(roots[g]), -1) if not top[g] else -1 for g in range(G)])
    stuck = gmap[labels] < 0
    labels = np.where(stuck, 0, gmap[labels])
    groups, reps_x = [], [reps_x[k] for k in keep]
    for i, k in enumerate(keep):
        idx = np.flatnonzero((labels == i) & ~stuck)
        groups.append({"sites": int(idx.size), "V": round(float(Vg[k]), 6),
                       "where": [round(float(x), 3) for x in inv[idx].mean(0)], "flat_dirs": int(flat[k])})
    if not groups:
        return np.full(shape, -1), []
    # a site is IN its valley when it lies within half the way from the valley to the border of its basin (the
    # midpoint to the nearest other valley, or with one valley the symmetric point); otherwise it is still between
    # (-1): on the top, in a wall or a core
    ref = np.empty(len(groups))
    for g in range(len(groups)):
        others = [0.5 * np.linalg.norm(reps_x[g] - reps_x[h]) for h in range(len(groups)) if h != g]
        far = float(np.linalg.norm(reps_x[g]))
        ref[g] = min(others) if others else (far if far > 1e-3 * vmax else np.sqrt(2.0) * vmax)
    inside = (moved < 0.5 * ref[labels]) & ~stuck
    # stable names: deepest first, then by position
    order = sorted(range(len(groups)), key=lambda g: (groups[g]["V"], groups[g]["where"]))
    remap = np.empty(len(groups), int)
    remap[order] = np.arange(len(groups))
    out = np.where(inside, remap[labels], -1)
    groups = [groups[g] for g in order]
    for g, G in enumerate(groups):
        G["inside"] = int((out == g).sum())
    return out.reshape(shape), groups


def _periodic_label(mask: np.ndarray) -> tuple[np.ndarray, int]:
    lab, n = ndimage.label(mask)
    if n == 0:
        return lab, 0
    lab = lt._merge_periodic(lab)
    _, lab = np.unique(lab, return_inverse=True)
    lab = lab.reshape(mask.shape)
    return lab, int(lab.max())


def _shape_descriptor(idx_list: list[np.ndarray], shape) -> np.ndarray:
    """Size and the normalised principal moments of a region (periodic: coordinates unwrapped around the circular
    mean). Two regions with the same descriptor to rounding have the same size and shape up to rotation."""
    pts = []
    for ax, ix in enumerate(idx_list):
        n = shape[ax]
        m = lt._circ_mean(ix, n, np.ones(ix.size))
        pts.append(((ix - m + n / 2) % n) - n / 2)
    P = np.stack(pts, 1).astype(float)
    P -= P.mean(0)
    ev = np.sort(np.linalg.eigvalsh(P.T @ P / len(P))) if len(P) > 1 else np.zeros(len(shape))
    return np.concatenate([[len(P)], ev])


def domains(labels: np.ndarray, min_size: int = 27) -> dict[str, Any]:
    """Connected regions per group, bonds between groups (by pair), plaquettes where ≥ 3 groups meet, and how
    different same-group regions of at least `min_size` sites are from each other."""
    d = labels.ndim
    per_group, descr = {}, []
    for g in np.unique(labels[labels >= 0]):
        lab, n = _periodic_label(labels == g)
        sizes = np.bincount(lab.ravel())[1:]
        per_group[int(g)] = {"regions": n, "regions_big": int((sizes >= min_size).sum()),
                             "largest": int(sizes.max()) if n else 0}
        for k in np.flatnonzero(sizes >= min_size):
            descr.append((int(g), _shape_descriptor(list(np.nonzero(lab == k + 1)), labels.shape)))
    pairs: dict[str, int] = {}
    K = int(labels.max()) + 1
    for ax in range(d):
        a, b = labels, ah._sh(labels, ax)
        m = (a != b) & (a >= 0) & (b >= 0)
        codes, counts = np.unique(np.minimum(a[m], b[m]) * K + np.maximum(a[m], b[m]), return_counts=True)
        for code, cnt in zip(codes, counts):
            key = f"{code // K}-{code % K}"
            pairs[key] = pairs.get(key, 0) + int(cnt)
    meet3 = 0
    for i, j in ah.planes(d):
        corners = np.stack([labels, ah._sh(labels, i), ah._sh(labels, j), ah._sh(ah._sh(labels, i), j)])
        srt = np.sort(np.where(corners >= 0, corners, -1), 0)
        distinct = (srt[0] >= 0).astype(int) + ((np.diff(srt, axis=0) != 0) & (srt[1:] >= 0)).sum(0)
        meet3 += int((distinct >= 3).sum())
    return {"groups": per_group, "regions": int(sum(v["regions"] for v in per_group.values())),
            "regions_big": int(sum(v["regions_big"] for v in per_group.values())),
            "between_fraction": round(float((labels < 0).mean()), 6),
            "bonds_between": pairs, "bonds_between_total": int(sum(pairs.values())),
            "plaquettes_3plus": meet3, "sameness": sameness([x[1] for x in descr], [x[0] for x in descr])}


def sameness(descr: list[np.ndarray], kind: list[Any]) -> dict[str, Any]:
    """Within each kind: the smallest relative difference between two members' descriptors, and how many pairs are
    identical to rounding (1e-9)."""
    out = {"members": len(descr), "kinds": {}}
    for k in sorted(set(kind), key=str):
        D = np.array([d for d, kk in zip(descr, kind) if kk == k])
        if len(D) < 2:
            out["kinds"][str(k)] = {"members": int(len(D))}
            continue
        scale = np.abs(D).mean(0) + 1e-12
        tree = cKDTree(D / scale)
        dist, _ = tree.query(D / scale, k=2)
        out["kinds"][str(k)] = {"members": int(len(D)), "closest_pair": round(float(dist[:, 1].min()), 6),
                                "median_nearest": round(float(np.median(dist[:, 1])), 6),
                                "identical_pairs": int(len(tree.query_pairs(1e-9)))}
    return out


# ------------------------------------------------------------------------------------------ windings
def windings(spec, st) -> dict[str, Any]:
    """Per complex field, the plaquettes its phase winds around (gauge-invariant with light, the plain phase
    without). With several fields: how many of those are shared by all fields."""
    c, th = st["c"], st["th"]
    if not spec["complex"]:
        return {}
    ths = th if spec["e"] else np.zeros_like(th)
    per, masks = [], []
    for a in range(spec["complex"]):
        w = ah.winding(c[a], ths)
        m = np.stack([w[p] != 0 for p in ah.planes(c[a].ndim)])
        per.append(int(m.sum()))
        masks.append(m)
    out = {"per_field": per}
    if len(masks) > 1:
        out["shared_by_all"] = int(np.logical_and.reduce(masks).sum())
    if spec["e"]:
        out["flux_mean"] = round(float(ah.flux_magnitude(th).mean()), 6)
    return out


# ------------------------------------------------------------------------------------------ lumps
def lumps(spec, st, thr_sigma: float = 3.0, min_size: int = 3) -> dict[str, Any]:
    """Regions of energy density above mean + thr_sigma·std that do not span more than half the box."""
    e = sb.energy_density(spec, st)
    thr = float(e.mean() + thr_sigma * e.std())
    lab, n = _periodic_label(e > thr)
    rho = sb.charge_density(st)
    Qa = [2.0 * np.imag(np.conj(st["c"][a]) * st["pc"][a]) for a in range(spec["complex"])]
    items, extended = [], 0
    for k in range(1, n + 1):
        sel = lab == k
        if sel.sum() < min_size:
            continue
        idx = np.nonzero(sel)
        ext = [lt._extent(idx[ax], e.shape[ax]) for ax in range(e.ndim)]
        if max(ext) > e.shape[0] // 2:
            extended += 1
            continue
        w = e[idx]
        items.append({"pos": tuple(lt._circ_mean(idx[ax], e.shape[ax], w) for ax in range(e.ndim)),
                      "size": int(sel.sum()), "content": float(w.sum()), "peak": float(w.max()),
                      "charge": round(float(rho[idx].sum()), 6),
                      "flavour_charges": [round(float(q[idx].sum()), 6) for q in Qa],
                      "descr": _shape_descriptor(list(idx), e.shape)})
    return {"threshold": thr, "lumps": items, "extended": extended}


def lump_kind(L: dict[str, Any], unit: float) -> tuple:
    """Rounded features: content in octaves of `unit`, the sign of each charge."""
    return (int(np.floor(np.log2(max(L["content"] / unit, 1e-12)))), int(np.sign(np.round(L["charge"], 3))),
            tuple(int(np.sign(np.round(q, 3))) for q in L["flavour_charges"]))


# ------------------------------------------------------------------------------------------ one frame
def census(spec, st, with_domains: bool = True) -> dict[str, Any]:
    a = sb.scale_factor(spec, st["tau"])
    s = sb.order_parameter(spec, st)
    out: dict[str, Any] = {"t": round(float(st["tau"]), 4), "a": round(a, 6), "energy": energy_parts(spec, st),
                           "s_mean": round(float(s.mean()), 6), "s_std": round(float(s.std()), 6),
                           "flavour_charges": [round(float(q), 6) for q in sb.flavor_charges(st)],
                           "gauss_max": float(np.abs(sb.gauss_residual(spec, st)).max())}
    if with_domains:
        labels, groups = label_sites(spec, st)
        out["valleys"] = groups
        out["domains"] = domains(labels)
        out["_labels"] = labels
    out["windings"] = windings(spec, st)
    L = lumps(spec, st)
    unit = float(np.median([x["content"] for x in L["lumps"]])) if L["lumps"] else 1.0
    kinds = [lump_kind(x, unit) for x in L["lumps"]]
    out["lumps"] = {"n": len(L["lumps"]), "extended": L["extended"], "threshold": round(L["threshold"], 6),
                    "kinds": {str(k): kinds.count(k) for k in sorted(set(kinds))},
                    "sameness": sameness([x["descr"] for x in L["lumps"]], kinds)}
    out["_lumps"] = L["lumps"]
    return out


# ------------------------------------------------------------------------------------------ ω–k
class Spectrum:
    """Collects the axis Fourier modes (k, 0, 0), (0, k, 0), (0, 0, k) of gauge-invariant local fields at equal time
    intervals; `result()` gives the power P(ω, k) averaged over the axes and its peaks."""

    def __init__(self, spec):
        self.spec, self.t, self.rows = spec, [], {}

    def channels(self, st) -> dict[str, np.ndarray]:
        spec, a = self.spec, sb.scale_factor(self.spec, st["tau"])
        ch = {f"real{i}": st["r"][i] / a for i in range(spec["real"])}
        for k in range(spec["complex"]):
            ch[f"|complex{k}|2"] = np.abs(st["c"][k] / a) ** 2
            if not spec["e"]:
                ch[f"Re complex{k}"] = (st["c"][k] / a).real
        if spec["e"]:
            d = st["th"].shape[0]
            ch["B"] = np.sin(ah.plaquette(st["th"], 0, 1)) if d >= 2 else None
        return {k: v for k, v in ch.items() if v is not None}

    def add(self, st) -> None:
        self.t.append(float(st["tau"]))
        for name, f in self.channels(st).items():
            F = np.fft.fftn(f) / f.size                              # k = 0: the uniform oscillation
            n = min(f.shape)
            modes = [F[(slice(0, n // 2 + 1),) + (0,) * (f.ndim - 1)]]
            for ax in range(1, f.ndim):
                idx = [0] * f.ndim
                idx[ax] = slice(0, n // 2 + 1)
                modes.append(F[tuple(idx)])
            self.rows.setdefault(name, []).append(np.stack(modes))

    def result(self, rel: float = 0.1) -> dict[str, Any]:
        t = np.array(self.t)
        if len(t) < 16:
            return {}
        dt = float(np.median(np.diff(t)))
        out = {"dt_sample": dt, "omega_nyquist": round(np.pi / dt, 4), "channels": {}}
        w = 2 * np.pi * np.fft.rfftfreq(len(t), dt)
        win = np.hanning(len(t))
        for name, rows in self.rows.items():
            X = np.stack(rows)                                        # (time, axes, k)
            X = X - X.mean(0)
            P = (np.abs(np.fft.fft(X * win[:, None, None], axis=0)) ** 2)[: len(w)].mean(1)   # (ω, k)
            n = P.shape[1]
            peaks = []
            for k in range(n):
                col = P[:, k]
                if col.max() <= 0:
                    peaks.append([])
                    continue
                pk = [i for i in range(1, len(col) - 1) if col[i] >= col[i - 1] and col[i] > col[i + 1]
                      and col[i] > rel * col.max()]
                peaks.append([round(float(w[i]), 4) for i in pk])
            out["channels"][name] = {"k": [round(2 * np.pi * k / (2 * (n - 1)), 4) for k in range(n)],
                                     "peaks": peaks,
                                     "branches_small_k": len(peaks[1]) if n > 1 else 0,
                                     "power_total": float(P.sum())}
        return out
