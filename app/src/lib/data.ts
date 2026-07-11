import type { Catalog, FieldDoc, RenderManifest, DecodedLens, LensDoc } from './types'

const BASE = import.meta.env.BASE_URL + 'data/'

export async function loadCatalog(): Promise<Catalog> {
  const r = await fetch(BASE + 'catalog.json')
  if (!r.ok) throw new Error('catalog fetch failed: ' + r.status)
  return r.json()
}

export async function loadField(roomId: string): Promise<FieldDoc | null> {
  const r = await fetch(BASE + 'rooms/' + roomId + '/field.json')
  if (!r.ok) return null
  return r.json()
}

export async function loadManifest(roomId: string): Promise<RenderManifest | null> {
  const r = await fetch(BASE + 'rooms/' + roomId + '/render-manifest.json')
  if (!r.ok) return null
  return r.json()
}

function b64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out
}

/** Restore a lens to normalized [0,1] values (uint8/255). Physical value = vmin + norm*(vmax-vmin). */
export function decodeLens(name: string, L: LensDoc, grid: number[], nframes: number): DecodedLens {
  const bytes = b64ToBytes(L.data_b64)
  const norm = new Float32Array(bytes.length)
  for (let i = 0; i < bytes.length; i++) norm[i] = bytes[i] / 255
  return {
    name, grid, nframes, cyclic: L.cyclic, vmin: L.vmin, vmax: L.vmax,
    unit: L.unit, source: L.source, norm,
  }
}

export function frameStride(grid: number[]): number {
  return grid.reduce((a, b) => a * b, 1)
}
