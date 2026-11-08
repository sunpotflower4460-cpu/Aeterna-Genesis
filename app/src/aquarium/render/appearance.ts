import type { Transfer } from '../types'

/** Display settings only. None of these values is sent to the simulation. */
export interface Appearance {
  palette: 'ice' | 'ember' | 'mono'
  quality: 'draft' | 'balanced' | 'fine'
  shading: boolean
  contours: boolean
  guides: boolean
  interpolate: boolean
  mode: 'volume' | 'surface' | 'slice'
  axis: 'x' | 'y' | 'z'
  slice: number
}
export const DEFAULT_APPEARANCE: Appearance = {
  palette: 'ice', quality: 'balanced', shading: true, contours: false, guides: true,
  interpolate: true, mode: 'volume', axis: 'z', slice: 0.5,
}
export const PALETTE_INDEX = { ice: 0, ember: 1, mono: 2 }
export const AXIS_INDEX = { x: 0, y: 1, z: 2 }
export const QUALITY_STEPS = { draft: 72, balanced: 144, fine: 240 }
export const MODE: Record<Transfer, number> = { high: 0, low: 1, cyclic: 2, diverging: 3 }

const mix = (a: number[], b: number[], t: number) => a.map((v, i) => v + (b[i] - v) * t)
/** Same anchors and expressions as the GPU palette; also used by legends and exported PNGs. */
export function displayColor(v: number, transfer: Transfer, palette: Appearance['palette']): number[] {
  const t = Math.max(0, Math.min(1, v))
  if (transfer === 'cyclic') {
    const h = t - Math.floor(t)
    return [0, 8, 4].map((n) => {
      const k = (n + h * 12) % 12
      return 0.59 - 0.76 * 0.41 * Math.max(-1, Math.min(k - 3, 9 - k, 1))
    })
  }
  if (transfer === 'diverging') return t < 0.5
    ? mix([0.12, 0.36, 0.65], [0.94, 0.95, 0.92], t * 2)
    : mix([0.94, 0.95, 0.92], [0.78, 0.22, 0.12], (t - 0.5) * 2)
  if (palette === 'mono') return mix([0.055, 0.075, 0.1], [0.94, 0.97, 1], transfer === 'low' ? 1 - t : t)
  if (palette === 'ember') {
    const q = transfer === 'low' ? 1 - t : t
    return q < 0.5 ? mix([0.13, 0.055, 0.12], [0.8, 0.28, 0.16], q * 2)
      : mix([0.8, 0.28, 0.16], [1, 0.9, 0.62], (q - 0.5) * 2)
  }
  if (transfer === 'low') return mix([0.96, 0.83, 0.48], [0.18, 0.69, 0.82], t)
  return t < 0.5 ? mix([0.025, 0.07, 0.16], [0.08, 0.58, 0.68], t * 2)
    : mix([0.08, 0.58, 0.68], [0.88, 0.98, 0.96], (t - 0.5) * 2)
}
export function colorCss(v: number, transfer: Transfer, palette: Appearance['palette']): string {
  return `rgb(${displayColor(v, transfer, palette).map((c) => Math.round(c * 255)).join(' ')})`
}
export function legendGradient(transfer: Transfer, palette: Appearance['palette']): string {
  return `linear-gradient(90deg, ${Array.from({ length: 17 }, (_, i) => `${colorCss(i / 16, transfer, palette)} ${i / 16 * 100}%`).join(', ')})`
}

export const COLOR_GLSL = /* glsl */ `
  uniform int uMode;
  uniform int uPalette;
  vec3 fieldColor(float t) {
    t = clamp(t, 0.0, 1.0);
    if (uMode == 2) {
      vec3 k = mod(vec3(0.0, 8.0, 4.0) + fract(t) * 12.0, 12.0);
      return 0.59 - 0.76 * 0.41 * clamp(min(k - 3.0, 9.0 - k), -1.0, 1.0);
    }
    if (uMode == 3) return t < 0.5
      ? mix(vec3(0.12,0.36,0.65),vec3(0.94,0.95,0.92),t*2.0)
      : mix(vec3(0.94,0.95,0.92),vec3(0.78,0.22,0.12),(t-0.5)*2.0);
    if (uPalette == 2) return mix(vec3(0.055,0.075,0.1),vec3(0.94,0.97,1.0),uMode == 1 ? 1.0-t : t);
    if (uPalette == 1) {
      float q = uMode == 1 ? 1.0-t : t;
      return q < 0.5 ? mix(vec3(0.13,0.055,0.12),vec3(0.8,0.28,0.16),q*2.0)
        : mix(vec3(0.8,0.28,0.16),vec3(1.0,0.9,0.62),(q-0.5)*2.0);
    }
    if (uMode == 1) return mix(vec3(0.96,0.83,0.48),vec3(0.18,0.69,0.82),t);
    return t < 0.5 ? mix(vec3(0.025,0.07,0.16),vec3(0.08,0.58,0.68),t*2.0)
      : mix(vec3(0.08,0.58,0.68),vec3(0.88,0.98,0.96),(t-0.5)*2.0);
  }
  vec2 decodeField(vec2 a, vec2 b, float blend, vec2 affineA, vec2 affineB) {
    if (uMode == 2) {
      // Interpolate on the unit circle, so +pi and -pi do not create a false zero-phase band.
      vec2 z = mix(a*2.0-1.0,b*2.0-1.0,blend);
      float amplitude = length(z);
      if (amplitude < 0.015) return vec2(0.0,0.0); // atan(0,0) is undefined; do not manufacture a direction.
      return vec2(fract(atan(z.y,z.x)/6.28318530718+1.0),smoothstep(0.015,0.08,amplitude));
    }
    return vec2(clamp(mix(a.r*affineA.x+affineA.y,b.r*affineB.x+affineB.y,blend),0.0,1.0),1.0);
  }
`
