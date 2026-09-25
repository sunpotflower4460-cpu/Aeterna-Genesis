import type { AquariumTemplate, TankField, TankLens } from './types'

const BASE = import.meta.env.BASE_URL + 'aquarium/'

export async function loadTemplates(): Promise<AquariumTemplate[]> {
  const r = await fetch(BASE + 'templates.json')
  if (!r.ok) throw new Error('templates fetch failed: ' + r.status)
  return (await r.json()).templates
}

function b64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out
}

export async function loadTank(id: string): Promise<TankField> {
  const r = await fetch(BASE + id + '/field.json')
  if (!r.ok) throw new Error('field fetch failed: ' + r.status)
  const d = await r.json()
  const lenses: Record<string, TankLens> = {}
  for (const name of Object.keys(d.lenses)) {
    const L = d.lenses[name]
    lenses[name] = {
      name, grid: d.grid, nframes: d.nframes, vmin: L.vmin, vmax: L.vmax, unit: L.unit,
      cyclic: !!L.cyclic, frames: b64ToBytes(L.data_b64),
    }
  }
  return { dimension: d.dimension, grid: d.grid, nframes: d.nframes, times: d.times, lenses }
}
