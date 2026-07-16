"""Phase-winding reliability observer (Loop-Trinity integration, Phase LT-2). role: V (measurement only).

WHY THIS EXISTS
A winding number read as round( sum(wrapped phase steps) / 2*pi ) along a closed line is only trustworthy
where the phase is well defined -- i.e. where the amplitude |psi| stays above the core scale and no single
step sits near +-pi (where +pi and -pi are indistinguishable). Reading an integer winding through a low-|psi|
core or across a near-pi ambiguous edge silently invents or drops charge. In the Aeterna-loop-trinity work,
"the winding recovered to 1" turned out to need a much stricter test than "the final majority is W=1": most
lines must be VALID (high enough amplitude, no near-pi edges) AND agree. This observer turns the amplitude
gate that is currently buried inside the defect *counters* into a first-class, per-line reliability report.

WHAT IT MEASURES (per closed line along `axis`, then aggregated; nothing about the physics changes)
  winding_integer            = round( sum(wrap(dphi)) / 2*pi )
  line_min_amplitude         = min |psi| along the line
  line_max_abs_phase_step    = max |wrap(dphi)|
  line_mean_abs_phase_step   = mean |wrap(dphi)|
  near_pi_step_count         = #edges with |wrap(dphi)| > pi - near_pi_margin   (ambiguous +pi/-pi)
  valid / invalid_reason     = valid iff line_min_amplitude >= amp_threshold AND near_pi_step_count == 0
Aggregate: winding histogram; dominant_winding and dominant_fraction OVER VALID LINES; invalid line
count/fraction with reasons; near-pi edge fraction; amplitude quantiles; and the closed-loop float residual
(a FLOAT-SANITY check only -- max |sum(wrap) - 2*pi*winding| -- never used as a reliability/phenomenon metric).

DISCIPLINE
- Diagnostic only: no physics/IC/law/artifact changes (no_touch; a NEW sibling module).
- Thresholds (amp_threshold, near_pi_margin) are RETURNED in the result so each experiment preregisters and
  per-model calibrates them. Loop's numeric values are NOT imported. amp_threshold defaults to a fraction of
  the field's own median line-amplitude (dimensionless), never a magic constant.
- Never claim "winding recovered / preserved" from the dominant winding alone: require high dominant_fraction
  AND low invalid_fraction (the observer reports both; it sets no pass/fail band).
- A large closed-loop residual means numerical trouble, not a physical phenomenon.
"""
import numpy as np

SIGN_CONVENTION = "winding = round(sum(wrap(phase[k+1]-phase[k]))/2pi) around the periodic line, +axis order"


def _wrap(d):
    return (d + np.pi) % (2.0 * np.pi) - np.pi


def winding_reliability(psi, axis=0, amp_frac=0.2, near_pi_margin=0.15, amp_threshold=None):
    """Per-line winding reliability along `axis` for a complex field, aggregated.

    Args:
        psi:            complex array (>=1D). Each "line" is the 1D periodic loop along `axis` for a fixed
                        transverse index.
        axis:           axis along which the closed loops run.
        amp_frac:       amp_threshold defaults to amp_frac * (median over lines of each line's mean |psi|).
        near_pi_margin: an edge with |wrapped step| > pi - near_pi_margin is flagged near-pi (ambiguous).
        amp_threshold:  absolute amplitude gate; overrides amp_frac when given.

    Returns dict (all thresholds echoed back for provenance): see module docstring for fields.
    """
    psi = np.asarray(psi, dtype=np.complex128)
    psi = np.moveaxis(psi, axis, 0)                       # lines run along axis 0
    L = psi.shape[0]
    flat = psi.reshape(L, -1)                             # (line_length, n_lines)
    amp = np.abs(flat)
    phase = np.angle(flat)
    # wrapped steps around the periodic loop (includes the wrap from last back to first)
    dstep = _wrap(np.diff(phase, axis=0, append=phase[:1]))   # shape (L, n_lines)
    line_sum = dstep.sum(axis=0)
    winding = np.rint(line_sum / (2.0 * np.pi)).astype(int)
    residual = np.abs(line_sum - 2.0 * np.pi * winding)       # float sanity only
    line_min_amp = amp.min(axis=0)
    line_mean_amp = amp.mean(axis=0)
    max_step = np.abs(dstep).max(axis=0)
    mean_step = np.abs(dstep).mean(axis=0)
    near_pi = np.abs(dstep) > (np.pi - near_pi_margin)        # (L, n_lines)
    near_pi_per_line = near_pi.sum(axis=0)

    thr = float(amp_threshold) if amp_threshold is not None else float(amp_frac * np.median(line_mean_amp))
    low_amp = line_min_amp < thr
    ambiguous = near_pi_per_line > 0
    valid = ~(low_amp | ambiguous)
    n_lines = int(flat.shape[1])

    reasons = {}
    if int(low_amp.sum()):
        reasons["low_amplitude"] = int((low_amp).sum())
    if int((ambiguous & ~low_amp).sum()):
        reasons["near_pi_ambiguous"] = int((ambiguous & ~low_amp).sum())

    # winding histogram and dominant winding OVER VALID LINES
    hist = {}
    for w in winding[valid]:
        hist[int(w)] = hist.get(int(w), 0) + 1
    n_valid = int(valid.sum())
    if n_valid:
        dom_w = max(hist, key=hist.get)
        dom_frac = hist[dom_w] / n_valid
    else:
        dom_w, dom_frac = None, 0.0

    return dict(
        axis=int(axis), n_lines=n_lines, line_length=int(L),
        amp_threshold=thr, amp_frac=float(amp_frac), near_pi_margin=float(near_pi_margin),
        dominant_winding=dom_w, dominant_fraction=float(dom_frac),
        winding_histogram={int(k): int(v) for k, v in sorted(hist.items())},
        valid_line_count=n_valid, invalid_line_count=int(n_lines - n_valid),
        invalid_fraction=float((n_lines - n_valid) / n_lines) if n_lines else 0.0,
        invalid_reasons=reasons,
        near_pi_edge_fraction=float(near_pi.mean()),
        amp_min=float(line_min_amp.min()), amp_median=float(np.median(line_min_amp)),
        amp_q10=float(np.quantile(line_min_amp, 0.10)),
        max_abs_phase_step=float(max_step.max()), mean_abs_phase_step=float(mean_step.mean()),
        closed_loop_residual_max=float(residual.max()),   # FLOAT SANITY ONLY
        sign_convention=SIGN_CONVENTION,
    )


# ------------------------------------------------------------------ synthetic controls (known answers)
def _uniform_winding_field(n=32, w=0, amp=1.0):
    """A clean field whose phase winds by integer w along axis 0 (constant amplitude)."""
    x = np.arange(n)
    phase = 2.0 * np.pi * w * x / n
    return (amp * np.exp(1j * phase))[:, None] * np.ones((1, n))


def _controls():
    out = []
    for w in (0, 1, 2):
        r = winding_reliability(_uniform_winding_field(32, w))
        out.append(("W%d clean" % w, r,
                    r["dominant_winding"] == w and r["dominant_fraction"] > 0.999 and r["invalid_fraction"] == 0.0))
    # low-amplitude line -> invalid (amplitude dips to ~0 along the loop)
    n = 32
    amp = np.abs(np.sin(np.pi * np.arange(n) / n))[:, None] * np.ones((1, n))    # 0 at x=0
    lowf = amp * np.exp(1j * 2 * np.pi * np.arange(n)[:, None] / n)
    r = winding_reliability(lowf)
    out.append(("low_amplitude_invalid", r, r["invalid_fraction"] > 0.0 and "low_amplitude" in r["invalid_reasons"]))
    # noise ladder -> reliability worsens (invalid fraction non-decreasing)
    rng = np.random.default_rng(0); base = _uniform_winding_field(48, 1)
    prev = -1.0; mono = True
    for a in (0.0, 0.3, 0.7, 1.2):
        rr = winding_reliability(base + a * (rng.standard_normal(base.shape) + 1j * rng.standard_normal(base.shape)))
        mono &= rr["invalid_fraction"] >= prev - 1e-9; prev = rr["invalid_fraction"]
    out.append(("noise_worsens_reliability", {"invalid_fraction": prev}, mono))
    return out


if __name__ == "__main__":
    allok = True
    for name, r, ok in _controls():
        allok &= ok
        extra = ("dom=%s frac=%.3f invalid=%.3f" % (r.get("dominant_winding"), r.get("dominant_fraction", 0),
                                                    r.get("invalid_fraction", 0)))
        print("  [%s] %-26s %s" % ("PASS" if ok else "FAIL", name, extra))
    print("STATUS:", "GREEN" if allok else "RED", "(role V: winding reliability observer; no physics changed)")
