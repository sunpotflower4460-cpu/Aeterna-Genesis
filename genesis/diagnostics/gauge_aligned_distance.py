"""Gauge-aligned complex-field distance (Loop-Trinity integration, Phase LT-1). role: V (measurement only).

WHY THIS EXISTS
A naive distance between two complex fields, D_raw = sqrt(mean |A-B|^2), grows even when A and B are the
SAME structure differing only by a global phase e^{i*theta} (a gauge/U(1) rotation). In the Aeterna-loop-trinity
work a "two structures fused / collapsed together" reading turned out, after this correction, to be "the same
structure all along, with a global phase offset that merely relaxed." So a large raw distance is NOT evidence of
structural change. This module separates the global-phase (gauge) part from the structural part so that claim is
never made by accident.

WHAT IT MEASURES (all real, dimensionless in field units; nothing about the physics is changed)
  raw_distance       = sqrt(mean_i |A_i - B_i|^2)                          # includes global-phase offset
  theta_star         = arg( sum_i A_i conj(B_i) )                          # best global phase to rotate B onto A
  aligned_distance   = sqrt(mean_i |A_i - e^{i theta_star} B_i|^2)         # STRUCTURAL distance (gauge removed)
  invariant_distance = sqrt( (sum|A|^2 + sum|B|^2 - 2|sum A conj(B)|)/N )  # closed form of the aligned minimum
  gauge_overlap      = |sum A conj(B)| / sqrt(sum|A|^2 sum|B|^2)           # 1 => identical up to global phase

SIGN CONVENTION (fixed and tested): theta_star = arg(sum A conj(B)); it is applied to the SECOND field:
  B_aligned = exp(i * theta_star) * B.  At that angle the aligned distance equals the invariant distance, which
  is the reason both are returned (they agree to floating tolerance -> a built-in self-check).

DISCIPLINE
- This is a diagnostic. It does NOT change any physics, IC, law, or artifact (no_touch: measures.py and all
  existing modules/Rooms are untouched; this is a NEW sibling module).
- Never call a large raw_distance a "structural collapse" / "fusion": use aligned_distance / invariant_distance
  for that, and gauge_overlap to see if the difference is purely global phase.
- Loop numeric thresholds are NOT imported; this module reports numbers, it sets no pass/fail band. Any
  recovery/identity threshold belongs to a preregistered experiment, per-model calibrated.
- Non-finite (NaN/inf) cells are excluded pairwise and counted (finite_count/total_count); zero-norm inputs are
  reported (zero_norm=True, gauge_overlap=None) rather than dividing by zero.
"""
import numpy as np

SIGN_CONVENTION = "theta_star = arg(sum A conj(B)); applied to the SECOND field as B_aligned = exp(i*theta_star)*B"


def gauge_aligned_distance(A, B, eps=1e-12):
    """Compare two complex fields separating the global-phase (gauge) part from the structural part.

    Args:
        A, B: array-likes of identical shape, cast to complex. Non-finite cells (NaN/inf in either) are
              excluded pairwise from every sum and reported via finite_count/total_count.
        eps:  norms at or below eps are treated as zero (overlap -> None, alignment -> undefined).

    Returns dict:
        raw_distance, aligned_distance, invariant_distance: float (RMS, field units)
        gauge_overlap: float in [0,1] or None (None if either field has ~zero norm over finite cells)
        theta_star: float radians or None (None if the cross term sum A conj(B) is ~0 -> alignment arbitrary)
        finite_count, total_count: int
        zero_norm: bool (True if A or B has ~zero norm over the finite cells)
        invariant_clip: float (magnitude of the negative value clipped to 0 in D_inv^2; 0.0 if none)
        sign_convention: str
    """
    A = np.asarray(A, dtype=np.complex128)
    B = np.asarray(B, dtype=np.complex128)
    if A.shape != B.shape:
        raise ValueError("A and B must have the same shape; got %s vs %s" % (A.shape, B.shape))
    total = int(A.size)
    finite = np.isfinite(A.real) & np.isfinite(A.imag) & np.isfinite(B.real) & np.isfinite(B.imag)
    n = int(finite.sum())
    if n == 0:
        return dict(raw_distance=float("nan"), aligned_distance=float("nan"), invariant_distance=float("nan"),
                    gauge_overlap=None, theta_star=None, finite_count=0, total_count=total, zero_norm=True,
                    invariant_clip=0.0, sign_convention=SIGN_CONVENTION)
    a = A[finite]; b = B[finite]
    raw = float(np.sqrt(np.mean(np.abs(a - b) ** 2)))
    na2 = float(np.sum(np.abs(a) ** 2)); nb2 = float(np.sum(np.abs(b) ** 2))
    C = complex(np.sum(a * np.conj(b)))                     # cross term
    absC = abs(C)
    zero_norm = (na2 <= eps) or (nb2 <= eps)
    overlap = None if zero_norm else float(absC / np.sqrt(na2 * nb2))
    # global-phase alignment (applied to B). If the cross term ~0, the optimal angle is undefined.
    if absC <= eps:
        theta_star = None
        aligned = raw                                        # no meaningful rotation -> equals raw
    else:
        theta_star = float(np.angle(C))
        b_aligned = np.exp(1j * theta_star) * b
        aligned = float(np.sqrt(np.mean(np.abs(a - b_aligned) ** 2)))
    # closed form of the aligned minimum: D_inv^2 = (|A|^2 + |B|^2 - 2|C|)/N
    inv_sq = (na2 + nb2 - 2.0 * absC) / n
    clip = float(-inv_sq) if inv_sq < 0.0 else 0.0          # tiny negatives are float error; record magnitude
    invariant = float(np.sqrt(max(0.0, inv_sq)))
    return dict(raw_distance=raw, aligned_distance=aligned, invariant_distance=invariant,
                gauge_overlap=overlap, theta_star=theta_star, finite_count=n, total_count=total,
                zero_norm=zero_norm, invariant_clip=clip, sign_convention=SIGN_CONVENTION)


# ------------------------------------------------------------------ synthetic controls (known answers)
def _controls():
    rng = np.random.default_rng(0)
    F = rng.normal(size=(16, 16)) + 1j * rng.normal(size=(16, 16))
    out = []
    # 1. identical fields -> all distances 0, overlap 1
    r = gauge_aligned_distance(F, F)
    out.append(("identical", r, r["raw_distance"] < 1e-9 and r["aligned_distance"] < 1e-9 and
                abs(r["gauge_overlap"] - 1.0) < 1e-9))
    # 2. same field + global phase pi/5 -> raw large, aligned ~0, overlap ~1
    r = gauge_aligned_distance(F, np.exp(1j * np.pi / 5) * F)
    out.append(("global_phase_pi/5", r, r["raw_distance"] > 0.1 and r["aligned_distance"] < 1e-9 and
                r["invariant_distance"] < 1e-9 and abs(r["gauge_overlap"] - 1.0) < 1e-9))
    # 3. structurally different field -> aligned stays > 0 (gauge cannot remove real difference)
    G = rng.normal(size=(16, 16)) + 1j * rng.normal(size=(16, 16))
    r = gauge_aligned_distance(F, G)
    out.append(("structurally_different", r, r["aligned_distance"] > 0.1))
    # 4. aligned == invariant (self-consistency)
    r = gauge_aligned_distance(F, np.exp(0.7j) * (F + 0.3 * G))
    out.append(("aligned==invariant", r, abs(r["aligned_distance"] - r["invariant_distance"]) < 1e-9))
    # 5. zero-norm second field -> overlap None, zero_norm True, no crash
    r = gauge_aligned_distance(F, np.zeros_like(F))
    out.append(("zero_norm", r, r["gauge_overlap"] is None and r["zero_norm"]))
    # 6. NaN rejection -> finite_count < total_count, finite result
    Fn = F.copy(); Fn[0, 0] = np.nan + 1j * np.inf
    r = gauge_aligned_distance(Fn, F)
    out.append(("nan_rejected", r, r["finite_count"] == F.size - 1 and np.isfinite(r["aligned_distance"])))
    return out


if __name__ == "__main__":
    allok = True
    for name, r, ok in _controls():
        allok &= ok
        print("  [%s] %-22s raw=%.4f aligned=%.4f inv=%.4f overlap=%s theta=%s"
              % ("PASS" if ok else "FAIL", name, r["raw_distance"], r["aligned_distance"],
                 r["invariant_distance"], None if r["gauge_overlap"] is None else round(r["gauge_overlap"], 4),
                 None if r["theta_star"] is None else round(r["theta_star"], 4)))
    print("STATUS:", "GREEN" if allok else "RED", "(role V: gauge-aligned distance observer; no physics changed)")
