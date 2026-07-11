// Colormaps map a MEASURED normalized value [0,1] to color. Cyclic lenses (phase) use a hue wheel;
// linear lenses use an ice ramp. The render-manifest records which lens is which — no arbitrary recolor.

function hslToRgb(h: number, s: number, l: number): [number, number, number] {
  const a = s * Math.min(l, 1 - l)
  const f = (n: number) => {
    const k = (n + h * 12) % 12
    return l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))
  }
  return [f(0), f(8), f(4)]
}

// ice ramp: deep blue -> teal/cyan -> near white
const RAMP: [number, [number, number, number]][] = [
  [0.0, [0.02, 0.05, 0.14]],
  [0.35, [0.05, 0.35, 0.5]],
  [0.65, [0.31, 0.89, 0.88]],
  [1.0, [0.92, 0.99, 1.0]],
]

function rampColor(t: number): [number, number, number] {
  t = Math.max(0, Math.min(1, t))
  for (let i = 1; i < RAMP.length; i++) {
    if (t <= RAMP[i][0]) {
      const [t0, c0] = RAMP[i - 1]
      const [t1, c1] = RAMP[i]
      const f = (t - t0) / (t1 - t0 || 1)
      return [c0[0] + (c1[0] - c0[0]) * f, c0[1] + (c1[1] - c0[1]) * f, c0[2] + (c1[2] - c0[2]) * f]
    }
  }
  return RAMP[RAMP.length - 1][1]
}

export function lensColor(norm: number, cyclic: boolean): [number, number, number] {
  if (cyclic) return hslToRgb(norm, 0.72, 0.56)
  return rampColor(norm)
}

/** alpha for volumetric additive point rendering: low per-point so overlapping cells accumulate a
 * glow instead of saturating to white. Linear lenses fade the low-value background out entirely. */
export function lensAlpha(norm: number, cyclic: boolean): number {
  if (cyclic) return 0.13
  return Math.pow(norm, 2.2) * 0.5
}
