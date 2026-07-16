#!/usr/bin/env python3
"""3D vortex-line / closed-loop tracer (Observer 3D, role V).

WHAT IT IS
Reconstructs a vortex LINE (not just a pierced-plaquette ballot) from a 3D complex field:
a piecewise-linear polyline through the lattice, closed into a loop when the line does not
touch the array's periodic seam. This is the missing step `genesis.diagnostics.plaquette_ledger`
explicitly stops short of ("a defect BALLOT, not a traced vortex curve; a vortex-core graph is
a later, explicitly-limited step" -- this module IS that later step).

METHOD (standard lattice construction, akin to vortex-line extraction from plaquette/flux data
in lattice gauge theory and superfluid vortex tracking)
Reuses `plaquette_ledger`'s per-orientation, per-slice signed winding maps (same convention,
same reliability gating -- no reimplementation) for all 3 face orientations (xy/yz/zx). Treating
each unit lattice CUBE as a control volume, the 3 plaquette orientations give exactly its 6 face
fluxes under a consistent right-handed convention (xy-plaquette normal=+z, yz-plaquette
normal=+x, zx-plaquette normal=+y -- the same cyclic x->y->z->x convention that relates
circulation on the 3 coordinate planes to the 3 components of vorticity). A vortex line pierces
a cube through exactly the faces with nonzero flux; for a single well-separated line this is
exactly 2 faces per cube, and the sum of all 6 signed face fluxes is 0 by construction (discrete
Gauss law -- checked and reported, never silently assumed). Connecting each pierced face's
center to its partner within every cube yields a graph where each interior pierced face has
degree exactly 2 (shared by its two neighboring cubes); walking that graph traces closed loops.

DANGLING-FACE HEALING (chain-endpoint-based reconnection, H021 campaign, 2026-07-16)
Where the line runs close to tangent to a coordinate plane (most common near a curved loop's
widest point), a cube may show only 1 pierced face instead of 2 -- a standard discretization gap
known from marching-cubes-style algorithms and lattice vortex-line extraction alike. These
"dangling" half-edges are reconnected via LOCAL healing, but not by naive nearest-neighbor
distance alone: the clean-cube graph is traced FIRST (before healing), and each open chain's
local tangent direction at its two endpoints is used to require that a healing partner look like
a plausible geometric CONTINUATION of the line -- both chains reaching toward each other, not
merely two fragments that happen to be nearby. This replaced a pure-distance heuristic after nine
rounds of external review repeatedly found edge cases in it (same-sign pairing, duplicate edges,
non-deterministic tie-breaks, two-sided faces re-entering the pool) -- individually patched each
time, but the underlying design (no notion of the line's direction of travel) kept producing new
ones. Isolated dangling faces with no attached clean chain (no tangent available) still fall back
to the original distance+sign-only criterion.

WHAT IT IS NOT (responsibility boundaries)
- NOT a claim about self-formed structure. This is a measurement instrument (role V); it reports
  geometry of whatever line is present, seeded or emergent, without judgment.
- NOT robust to multiple simultaneous CLOSE or CROSSING lines: a cube with more than 2 pierced
  faces, or with exactly 2 pierced faces whose fluxes don't actually cancel (same sign, or
  |flux|>1), is reported as `ambiguous_cubes`, never silently paired by heuristic.
- Does NOT trace across the array's index-0/index-(L-1) seam: `plaquette_ledger` does not compute
  the wraparound plaquette (its winding arrays have L-1 valid entries, not L, along each in-plane
  axis), so a line that approaches the box edge is reported as an OPEN path there, not a closed
  loop. Validation runs (e.g. the seeded ring of e003) keep the line away from this seam by
  construction (`axial_margin`-style bulk placement); this is a real scope limit, not silently
  patched over.
- Curvature: the reported `mean_curvature` is a general discrete (turning-angle) estimate, valid
  for ANY loop shape. `effective_radius = length / (2*pi)` is reported alongside ONLY as a
  circular-loop comparison number (useful for a seeded ring where the true radius is known) --
  it is explicitly not a general shape descriptor and is labeled as such in the output.

v1 (`genesis.diagnostics.plaquette_ledger`) is UNCHANGED; this is an additive sibling instrument
(no_touch discipline, same pattern as LT-1/2/3 relative to `measures.py`).
"""
import numpy as np

from genesis.diagnostics.plaquette_ledger import _orientation


def face_windings(psi, amp_frac=0.2, near_pi_margin=0.15, amp_threshold=None):
    """Per-face signed winding for all 3 orientations of a 3D complex field.

    Returns (W_xy, W_yz, W_zx, threshold):
      W_xy[i, j, k]: winding of the xy-plaquette at corner (i,i+1)x(j,j+1), evaluated at z=k
        (face normal +z). Shape (L0-1, L1-1, L2).
      W_yz[i, j, k]: winding of the yz-plaquette at corner (j,j+1)x(k,k+1), evaluated at x=i
        (face normal +x). Shape (L0, L1-1, L2-1).
      W_zx[i, j, k]: winding of the zx-plaquette at corner (i,i+1)x(k,k+1), evaluated at y=j
        (face normal +y). Shape (L0-1, L1, L2-1).
    Same sign convention and reliability gating as `plaquette_ledger.plaquette_ledger`.
    """
    psi = np.asarray(psi, dtype=np.complex128)
    if psi.ndim != 3:
        raise ValueError("face_windings requires a 3D complex field; got ndim=%d" % psi.ndim)
    thr = float(amp_threshold) if amp_threshold is not None else float(amp_frac * np.median(np.abs(psi)))
    _s_xy, wmaps_xy = _orientation(psi, (0, 1), thr, near_pi_margin)   # sliced over z
    _s_yz, wmaps_yz = _orientation(psi, (1, 2), thr, near_pi_margin)   # sliced over x
    _s_zx, wmaps_zx = _orientation(psi, (0, 2), thr, near_pi_margin)   # sliced over y
    W_xy = np.stack(wmaps_xy, axis=2).astype(int)   # (L0-1, L1-1, L2)
    W_yz = np.stack(wmaps_yz, axis=0).astype(int)   # (L0, L1-1, L2-1)
    # _orientation's CCW loop for ("zx", (0, 2)) treats its own axis0=x as "horizontal" and
    # axis1=z as "vertical" (same convention _slice_ledger uses for every orientation), whose
    # right-hand-rule normal is x_hat x z_hat = -y_hat, NOT +y_hat -- unlike xy (x_hat x y_hat =
    # +z_hat) and yz (y_hat x z_hat = +x_hat), which DO follow the +axis cyclic pattern directly.
    # Negate here so W_zx consistently means "+y flux", matching how _cube_faces uses it (found by
    # external review, 2026-07-16: without this the signed 6-face divergence check was wrong
    # whenever a cube mixed a yz-face and a zx-face, e.g. near a curved line's tangent regions --
    # confirmed by re-deriving the convention and empirically on the ring synthetic, where 32 of
    # 56 "divergence violations" vanished once this sign was corrected).
    W_zx = -np.stack(wmaps_zx, axis=1).astype(int)   # (L0-1, L1, L2-1)
    return W_xy, W_yz, W_zx, thr


def _cube_faces(i, j, k, W_xy, W_yz, W_zx):
    """The 6 signed outward face fluxes of unit cube (i,j,k) as (face_id, flux) pairs, flux=0 omitted."""
    faces = [
        (("z", i, j, k), -int(W_xy[i, j, k])),
        (("z", i, j, k + 1), +int(W_xy[i, j, k + 1])),
        (("x", i, j, k), -int(W_yz[i, j, k])),
        (("x", i + 1, j, k), +int(W_yz[i + 1, j, k])),
        (("y", i, j, k), -int(W_zx[i, j, k])),
        (("y", i, j + 1, k), +int(W_zx[i, j + 1, k])),
    ]
    return faces


def _face_center(face_id):
    kind, a, b, c = face_id
    if kind == "z":
        return (a + 0.5, b + 0.5, float(c))
    if kind == "x":
        return (float(a), b + 0.5, c + 0.5)
    return (a + 0.5, float(b), c + 0.5)   # kind == "y"


def _trace_graph(neighbors):
    """Walk a face_id adjacency graph (face_id -> list of neighbor face_ids) into closed loops
    and open paths (each a list of face_ids). Shared by the pre-healing trace of the clean-only
    graph (used to derive chain-endpoint tangents, see `_chain_tangent`) and the final
    post-healing trace (used to build the returned geometry) -- the same walk logic, just run
    twice on two different snapshots of the same graph structure."""
    degree = {f: len(v) for f, v in neighbors.items()}
    visited = set()
    loops, open_paths = [], []

    def walk(start, first_next):
        path = [start]
        visited.add(start)
        prev, cur, nxt = start, start, first_next
        while True:
            path.append(nxt)
            if nxt == start:
                return path[:-1], True
            if nxt in visited:
                return path, False
            if degree.get(nxt, 0) != 2:
                # a genuine terminal endpoint (degree 1, e.g. a seam hit) -- mark it visited so
                # the outer scan doesn't walk the SAME chain a second time (backwards) starting
                # from here, which would report one open chain as two duplicate/reversed
                # fragments (found by external review, 2026-07-16: an earlier version of this fix
                # moved walking to start from endpoints first, but still left the FAR endpoint of
                # that walk unmarked).
                visited.add(nxt)
                return path, False
            visited.add(nxt)
            nbrs = neighbors[nxt]
            prev, cur = cur, nxt
            nxt = nbrs[0] if nbrs[0] != prev else nbrs[1]

    # Open paths FIRST, starting from actual endpoints (degree==1): walking from an endpoint
    # covers the whole chain (interior degree-2 nodes to the OTHER endpoint) in one pass, marking
    # every node on it visited. Starting from an arbitrary INTERIOR degree-2 node instead (as an
    # earlier version of this loop did) only follows ONE of its two directions, splitting a single
    # open chain into two separate fragments once dict-iteration order later reaches nodes on the
    # other side -- found by external review, 2026-07-16, before any real run had produced an open
    # chain to catch it on.
    for f in list(neighbors.keys()):
        if f in visited or degree.get(f, 0) != 1:
            continue
        path, closed = walk(f, neighbors[f][0])
        open_paths.append(path)   # degree==1 start can never close back on itself
    # closed loops: only unvisited degree-2 nodes remain -- any open chain was fully consumed above
    for f in list(neighbors.keys()):
        if f in visited or degree.get(f, 0) != 2:
            continue
        path, closed = walk(f, neighbors[f][0])
        if closed and len(path) >= 3:
            loops.append(path)
        elif not closed:
            open_paths.append(path)   # safety net for any residual fragment; honestly reported
    return loops, open_paths


def _chain_tangent(face_path, at_end):
    """Unit vector at one end of an open chain (face_id list, >=2 points), pointing 'outward' --
    the direction the chain is heading as it approaches that endpoint. Used by healing to judge
    whether a candidate partner looks like a plausible geometric CONTINUATION of this chain
    (chain-endpoint-based reconnection), not merely the nearest raw point. Returns None for a
    degenerate (<2 point, or zero-length last segment) chain -- callers must treat that as "no
    directional information available" and fall back to the distance+sign-only criterion."""
    if len(face_path) < 2:
        return None
    p_from, p_to = (face_path[-2], face_path[-1]) if at_end else (face_path[1], face_path[0])
    v = np.array(_face_center(p_to)) - np.array(_face_center(p_from))
    norm = float(np.linalg.norm(v))
    return v / norm if norm > 1e-12 else None


def trace_vortex_lines(psi, amp_frac=0.2, near_pi_margin=0.15, amp_threshold=None, max_heal_distance=3.0):
    """Trace closed vortex-line loops (and report any open/ambiguous paths) in a 3D complex field.

    max_heal_distance: cap on how far apart two dangling half-edges may be to heal via
    nearest-neighbor reconnection (see the note above the healing loop below for why this exists
    -- without a cap, sparse/pathological configurations could bridge two UNRELATED distant
    defects into one artificial loop; found by external review, 2026-07-16). Default 3.0 grid
    units comfortably covers the local tangent-region gaps this healing targets (observed at
    1-3 units in this module's own tests) while refusing anything genuinely distant.

    Returns a dict:
      loops: list of {points (ordered face-center coords, closed), length, centroid,
             mean_curvature, effective_radius, n_points, mean_abs_winding}
      open_paths: list of {points, length} for paths that hit the array seam or a degree!=2 node,
             including single-point (n_points=1) entries for an isolated unhealed dangling face
             that has no clean-cube-side connection either (never silently dropped)
      n_cubes_checked, n_cubes_pierced, n_cubes_overloaded (more than 2 pierced faces, or exactly
             2 pierced faces whose fluxes don't cancel -- these cubes are skipped, not guessed
             at), n_direction_rejected_pairs (candidate healing pairs that passed sign+distance
             but were rejected because their chains don't point toward each other -- see
             DANGLING-FACE HEALING in the module docstring; already reflected in
             n_unhealed_dangling, reported separately so the direction filter's own effect is
             visible), n_divergence_violations (sum of the 6 face fluxes != 0 -- should be 0 by
             construction; nonzero only at reliability-gated plaquettes, reported honestly, never
             hidden)
      threshold: the amplitude threshold used (provenance)
    """
    W_xy, W_yz, W_zx, thr = face_windings(psi, amp_frac, near_pi_margin, amp_threshold)
    L0m, L1m, L2 = W_xy.shape   # cube ranges: i in [0,L0m-1), j in [0,L1m-1), k in [0,L2-1)
    n_cubes_i, n_cubes_j, n_cubes_k = L0m, L1m, L2 - 1

    # Find candidate cubes cheaply: only cubes touching a nonzero face can be pierced.
    candidates = set()
    for arr, kind in ((W_xy, "z"), (W_yz, "x"), (W_zx, "y")):
        for idx in np.argwhere(arr != 0):
            a, b, c = (int(v) for v in idx)
            if kind == "z":
                for kk in (c - 1, c):
                    if 0 <= kk < n_cubes_k:
                        candidates.add((a, b, kk))
            elif kind == "x":
                for ii in (a - 1, a):
                    if 0 <= ii < n_cubes_i:
                        candidates.add((ii, b, c))
            else:
                for jj in (b - 1, b):
                    if 0 <= jj < n_cubes_j:
                        candidates.add((a, jj, c))

    # A cube is "clean" when exactly 2 of its 6 faces are pierced with unit, opposite-sign flux --
    # the line enters one, exits the other, and connecting their centers is unambiguous. A cube
    # with MORE than 2 pierced faces, or with 2 pierced faces that don't cancel (same sign, or
    # |flux|>1), is a genuine multi-line ambiguity (n_cubes_overloaded) and is skipped, never
    # guessed at. A cube with EXACTLY 1 pierced face ("dangling") is NOT a multi-line ambiguity -- it is
    # the standard discretization gap of this construction near a cube that the line grazes near
    # an edge/corner rather than passing cleanly through two faces (most common where the line
    # runs close to tangent to a coordinate plane, e.g. near a curved ring's widest point). This
    # is the same "ambiguous cube" case known from marching-cubes-style algorithms and from
    # lattice vortex-line extraction (e.g. P-vortex tracing in lattice gauge theory): the
    # standard, honest resolution is LOCAL nearest-neighbor reconnection of the leftover dangling
    # half-edges, counted and reported explicitly (n_cubes_dangling / n_healed_connections), never
    # silently absorbed into "clean" cubes.
    #
    # Divergence (the signed sum of all 6 face fluxes) is reported as a SEPARATE honesty
    # diagnostic (n_divergence_violations), not used to reclassify a pierced-2 cube: reliability
    # gating (near_pi_margin / amp_threshold, see plaquette_ledger) can zero out a TRUE nonzero
    # winding on a 3rd/4th face of the same cube, which breaks the discrete Gauss-law identity
    # without meaning the 2 faces we DO see are the wrong pair -- in practice the visible pair
    # remains the best available entry/exit estimate. A large divergence-violation count is a
    # signal to loosen the reliability gate for that field, not evidence the pairing is wrong.
    neighbors = {}     # face_id -> list of neighbor face_ids (via a shared cube or a healed pairing)
    n_overloaded = 0
    n_div_violations = 0
    n_pierced = 0
    dangling_raw = []
    for (i, j, k) in candidates:
        faces = _cube_faces(i, j, k, W_xy, W_yz, W_zx)
        total_flux = sum(f for _, f in faces)
        if total_flux != 0:
            n_div_violations += 1
        pierced = [(fid, f) for fid, f in faces if f != 0]
        if not pierced:
            continue
        n_pierced += 1
        # A pierced face with |flux| > 1 (a charge>=2 line, or two lines passing through the same
        # face) is NOT a simple single-line pass-through even when exactly 2 faces are pierced --
        # treating it as an ordinary clean pair would silently collapse the multiplicity into one
        # loop instead of flagging the genuine multi-line ambiguity this module promises to report,
        # not guess at (found by external review, 2026-07-16).
        # A 2-pierced cube with SAME-sign unit fluxes is also not an ordinary pass-through: a
        # single line entering one face and exiting another has opposite-sign outward flux at the
        # two faces by construction (their sum must be part of the cube's zero net divergence).
        # Same-sign faces mean the two visible fluxes don't actually cancel -- pairing them anyway
        # would silently join what may be two unrelated sources/sinks (e.g. from reliability gating
        # zeroing a true 3rd/4th face) into a fabricated segment. Routed to n_cubes_overloaded, the
        # same "ambiguous, skipped, never guessed at" bucket as >2-pierced cubes (found by external
        # review, 2026-07-16).
        if len(pierced) == 2 and all(abs(f) == 1 for _, f in pierced) and sum(f for _, f in pierced) == 0:
            a, b = (fid for fid, _ in pierced)
            neighbors.setdefault(a, []).append(b)
            neighbors.setdefault(b, []).append(a)
        elif len(pierced) == 1 and abs(pierced[0][1]) == 1:
            # Keep the sign, not just the face_id: a dangling half-edge's outward-flux sign
            # records whether the (reliability-gated-out) line enters or exits its cube through
            # this face, exactly like a clean pair's two faces. Discarding it and healing purely
            # by distance could pair two same-sign endpoints (two exits, or two entries) into an
            # artificial segment instead of leaving them ambiguous -- the same physical
            # inconsistency the same-sign clean-pair fix above addresses, just not yet applied to
            # healing (found by external review, 2026-07-16).
            dangling_raw.append((pierced[0][0], int(pierced[0][1])))
        else:
            n_overloaded += 1

    # A face can be the sole pierced face of BOTH its neighboring cubes independently (a shared
    # face is at most 2-sided, so this happens at most once per face), appending it to
    # dangling_raw twice with opposite signs, by construction -- adjacent cubes' outward normals
    # at a shared face are opposite. This two-sided case already represents a complete tangent
    # pass-through seen from both neighbors and needs no external connection at all -- it is
    # EXCLUDED from the pairing pool entirely (not merely deduplicated to one arbitrarily-signed
    # entry, which an earlier version of this fix did: that still left the face eligible for the
    # distance-based healing pass, so it could be healed to an unrelated nearby endpoint, or not,
    # purely depending on which of the two opposite signs happened to survive dedup -- found by
    # external review, 2026-07-16). Reported directly as its own isolated 1-point open path,
    # alongside genuinely-unhealed single-sided dangling faces (below).
    face_counts = {}
    for fid, _sign in dangling_raw:
        face_counts[fid] = face_counts.get(fid, 0) + 1
    seen_faces = set()
    dangling = []
    two_sided_isolated = []
    for fid, sign in dangling_raw:
        if fid in seen_faces:
            continue
        seen_faces.add(fid)
        if face_counts[fid] > 1:
            two_sided_isolated.append(fid)
        else:
            dangling.append((fid, sign))
    # Sort by face_id for a well-defined, reviewable tie-break rule: `dangling_raw`'s order
    # otherwise depends on iteration order of `candidates` (a set), so two equal-distance healing
    # candidates -- not uncommon for lattice-symmetric synthetic fields -- could be resolved by
    # incidental set-construction order rather than any deliberate geometric rule (found by
    # external review, 2026-07-16).
    dangling.sort(key=lambda t: t[0])

    # Chain-endpoint-based reconnection (H021 campaign, 2026-07-16): at this point `neighbors`
    # holds ONLY clean-cube pairing edges (healing hasn't run yet), so tracing it now recovers
    # every already-formed chain fragment. An open chain's two endpoints are exactly the faces
    # healing needs to extend outward; the chain's last segment gives a local tangent direction
    # at each endpoint -- the direction the line is heading as it approaches that end. A
    # candidate healing partner is only a plausible CONTINUATION of the line if both chains are
    # heading roughly toward each other, not merely nearby -- replacing pure nearest-neighbor
    # distance with a geometric plausibility check. This directly targets the failure mode nine
    # rounds of external review kept finding edge cases in: per-face nearest-neighbor pairing
    # has no notion of the line's direction of travel, so it can connect two fragments that
    # happen to be close but point in unrelated (or opposite) directions. Isolated dangling
    # faces with no clean-chain attached (no tangent available) fall back to the original
    # distance+sign-only criterion, unchanged.
    _clean_loops_unused, clean_open_chains = _trace_graph(neighbors)
    endpoint_tangent = {}
    for chain in clean_open_chains:
        t_start = _chain_tangent(chain, at_end=False)
        if t_start is not None:
            endpoint_tangent[chain[0]] = t_start
        t_end = _chain_tangent(chain, at_end=True)
        if t_end is not None:
            endpoint_tangent[chain[-1]] = t_end

    n_healed = 0
    n_direction_rejected = 0
    if dangling:
        pts = np.array([_face_center(fid) for fid, _ in dangling])
        # Cap healing to max_heal_distance: without a cutoff, a sparse/noisy field could bridge
        # two unrelated distant dangling faces (e.g. one near a real gap, one at the non-periodic
        # seam) into an artificial connection -- turning a genuinely open/separate path into a
        # fake closed loop, exactly the failure this module promises NOT to silently commit
        # (found by external review, 2026-07-16). Pairs beyond the cap are left unhealed.
        pairs_dist = []
        for a in range(len(dangling)):
            for b in range(a + 1, len(dangling)):
                if dangling[a][1] == dangling[b][1]:
                    # same sign: both "entries" or both "exits" -- cannot represent one continuous
                    # line crossing the gap (found by external review, 2026-07-16).
                    continue
                d = float(np.linalg.norm(pts[a] - pts[b]))
                if d > max_heal_distance:
                    continue
                fa, fb = dangling[a][0], dangling[b][0]
                if fb in neighbors.get(fa, ()):
                    # Already directly connected via a clean-cube pairing (e.g. both faces of the
                    # SAME clean 2-pierced cube are also each the sole pierced face of their OTHER
                    # respective neighbor). Such a pair's own chain tangents necessarily point
                    # AWAY from each other (they are the two ends of the very same 2-node chain),
                    # so the direction filter below would always reject it -- never reaching the
                    # existing-edge handling downstream, and wrongly counting both faces as
                    # unhealed even though they are already fully resolved. Skip direction
                    # filtering for already-connected pairs and let the downstream loop's
                    # already-connected check (matching on `fb in neighbors.get(fa, ())` again)
                    # mark them resolved, exactly as it does for such pairs found by distance
                    # alone (found by external review, 2026-07-16).
                    pairs_dist.append((d, a, b))
                    continue
                ta = endpoint_tangent.get(fa)
                tb = endpoint_tangent.get(fb)
                if ta is not None and tb is not None:
                    disp = (pts[b] - pts[a]) / d if d > 1e-12 else (pts[b] - pts[a])
                    # chain a must head toward b (positive dot with a's outward tangent), and
                    # chain b must head toward a (i.e. AWAY from b along -disp, so negative dot
                    # with b's own outward tangent measured along +disp) -- both chains reaching
                    # for each other, not just one passing near the other's tip.
                    if np.dot(disp, ta) <= 0.0 or np.dot(disp, tb) >= 0.0:
                        n_direction_rejected += 1
                        continue
                pairs_dist.append((d, a, b))
        pairs_dist.sort(key=lambda t: (t[0], t[1], t[2]))
        used = set()
        for _dist, a, b in pairs_dist:
            if a in used or b in used:
                continue
            fa, fb = dangling[a][0], dangling[b][0]
            if fb in neighbors.get(fa, ()):
                # Already directly connected via a clean-cube pairing -- e.g. both faces of the
                # SAME clean 2-pierced cube happen to also be the sole pierced face of their OTHER
                # respective neighbors, making them both "dangling" and geometrically close enough
                # for this healing pass to reconsider them. Adding a second identical edge would
                # create a duplicate degree-2 pair that collapses into a spurious 2-node closed
                # component, silently dropped by the len(path)>=3 filter downstream instead of
                # being reported (found by external review, 2026-07-16). Already resolved: mark
                # used, but do not add a redundant edge or count a healing. Not counted as
                # unhealed either -- this endpoint already has its one legitimate connection (a
                # dangling cube has exactly one pierced face, so it can only ever need exactly one
                # connection; it already has it via the clean pair), so it is not actually
                # unresolved (considered and consciously skipped, external review, 2026-07-16).
                used.add(a)
                used.add(b)
                continue
            neighbors.setdefault(fa, []).append(fb)
            neighbors.setdefault(fb, []).append(fa)
            used.add(a)
            used.add(b)
            n_healed += 1
        unpaired = [dangling[a][0] for a in range(len(dangling)) if a not in used]
    else:
        unpaired = []
    n_unhealed_dangling = len(unpaired)
    # A dangling face that stayed unhealed AND has no connection from the clean-cube-pairing pass
    # either (i.e. it never became a key of `neighbors` at all -- the neighboring cube across that
    # face isn't itself part of any clean pair) would otherwise be counted in n_unhealed_dangling
    # but be entirely invisible in the returned geometry, contradicting the "never silently
    # dropped" promise for open_paths. Surfaced explicitly as a single-point open path (found by
    # external review, 2026-07-16). A face that DID get a clean-cube-side connection is already a
    # degree-1 node in `neighbors` and is picked up naturally by the endpoint walk below.
    isolated_unhealed = [f for f in unpaired if f not in neighbors]

    # Final trace, on the graph now including healed edges: reuses the exact same walk logic as
    # the pre-healing trace above (`_trace_graph`), since the graph's structure -- not the source
    # of any given edge -- is all that logic depends on.
    final_loops, final_open_paths = _trace_graph(neighbors)
    # two_sided_isolated faces were excluded from the pairing pool entirely (see above) and can
    # never be a clean-cube-side neighbor either (a cube is either "dangling" with exactly 1
    # pierced face or part of a "clean pair" with exactly 2 -- never both), so they are always
    # structurally isolated; surfaced the same way as isolated_unhealed, never silently dropped.
    loops = final_loops
    open_paths = [[f] for f in isolated_unhealed + two_sided_isolated] + final_open_paths

    def _summarize_loop(face_path):
        pts = np.array([_face_center(f) for f in face_path], dtype=float)
        pts_closed = np.vstack([pts, pts[0]])
        seg = np.diff(pts_closed, axis=0)
        seg_len = np.linalg.norm(seg, axis=1)
        length = float(np.sum(seg_len))
        centroid = tuple(float(v) for v in pts.mean(axis=0))
        n = len(pts)
        curvatures = []
        for idx in range(n):
            v_in = pts_closed[idx] - pts_closed[idx - 1] if idx > 0 else pts_closed[0] - pts_closed[-2]
            v_out = pts_closed[idx + 1] - pts_closed[idx]
            len_in, len_out = np.linalg.norm(v_in), np.linalg.norm(v_out)
            if len_in < 1e-12 or len_out < 1e-12:
                continue
            cos_t = np.clip(np.dot(v_in, v_out) / (len_in * len_out), -1.0, 1.0)
            theta = float(np.arccos(cos_t))
            curvatures.append(theta / (0.5 * (len_in + len_out)))
        mean_curv = float(np.mean(curvatures)) if curvatures else 0.0
        return dict(points=[tuple(float(x) for x in p) for p in pts], length=length, centroid=centroid,
                    mean_curvature=mean_curv, effective_radius=length / (2.0 * np.pi), n_points=n)

    def _summarize_open(face_path):
        pts = np.array([_face_center(f) for f in face_path], dtype=float)
        seg_len = np.linalg.norm(np.diff(pts, axis=0), axis=1) if len(pts) > 1 else np.array([])
        return dict(points=[tuple(float(x) for x in p) for p in pts], length=float(np.sum(seg_len)),
                    n_points=len(pts))

    return dict(
        loops=[_summarize_loop(p) for p in loops],
        open_paths=[_summarize_open(p) for p in open_paths],
        n_cubes_checked=len(candidates), n_cubes_pierced=n_pierced,
        n_cubes_overloaded=n_overloaded,
        # n_cubes_dangling counts CUBES (matching its name), not unique faces: when a face is the
        # sole pierced face of BOTH its neighboring cubes, that's 2 dangling cubes contributing 2
        # separate divergence violations, even though they share one unique face and are
        # deduplicated to one pairing target in `dangling`. Using len(dangling) here undercounted
        # exactly this case, breaking the n_divergence_violations == n_cubes_dangling invariant
        # this module's own regression test checks (found by external review, 2026-07-16).
        n_cubes_dangling=len(dangling_raw),
        n_healed_connections=n_healed, n_unhealed_dangling=n_unhealed_dangling,
        # An opposite-sign-and-within-distance candidate pair (same-sign pairs are already
        # filtered out above and never reach this check) that was rejected specifically because
        # its two chains point away from (or sideways to) each other, not toward each other --
        # i.e. a pair the OLD pure-distance heuristic would have healed but chain-endpoint
        # reconnection judged geometrically implausible. Reported separately from
        # n_unhealed_dangling (which already includes these faces) so the effect of the
        # direction filter itself is visible, not folded silently into a generic count
        # (H021 campaign, 2026-07-16).
        n_direction_rejected_pairs=n_direction_rejected,
        n_divergence_violations=n_div_violations,
        threshold=thr,
        scope_note=("piecewise-linear line reconstruction from plaquette winding data; does not "
                    "trace across the array's periodic seam (see module docstring); cubes with "
                    ">2 pierced faces, or 2 pierced faces whose fluxes don't cancel (multi-line "
                    "ambiguity), are skipped and counted, never guessed at; cubes with exactly 1 "
                    "pierced face (a standard discretization gap near tangent/grazing regions) are "
                    "healed via nearest-neighbor reconnection, "
                    "counted in n_healed_connections; any leftover after healing is "
                    "n_unhealed_dangling, never silently dropped."),
    )
