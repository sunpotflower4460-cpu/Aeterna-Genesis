// Client for the live lab server (tools/lab/server.py). Same origin as the app when served by the lab
// server; in `npm run dev` Vite proxies /api to 127.0.0.1:8765. With --lan the server prints a token that
// arrives here as ?token=… and is kept for this tab only.

import type { Transfer } from '../aquarium/types'

export interface KnobSpec {
  name: string; label: string; kind: 'law' | 'start' | 'arg'
  default: number; lo: number; hi: number; step: number; integer: boolean
}
export interface LensSpec { name: string; label: string; transfer: Transfer; vmin: number; vmax: number; cyclic: boolean }
export interface PerturbSpec { name: string; label: string; args: KnobSpec[] }
export interface WhiteSpec {
  id: string; title: string; family: string; model: string; dimension: 2 | 3; grid: number[]
  steps_per_frame: number; dt: number; knobs: KnobSpec[]; lenses: LensSpec[]; perturbs: PerturbSpec[]
  put_in: string[]; source: string; ceiling_ref: string
}
export interface LabEvent { step: number; kind: 'set' | 'perturb'; values?: Record<string, number>; name?: string; args?: Record<string, number> }
export interface Recipe { white: string; seed: number; knobs: Record<string, number>; events: LabEvent[] }
export interface UniverseInfo {
  id: string; label: string; white: string; title: string; dimension: 2 | 3
  parent: string | null; branch_step: number | null; fork_index: number | null; recipe: Recipe; put_in: string[]
  step: number; t: number; playing: boolean; speed: number; metrics: Record<string, number>; diverged: boolean; alive: boolean
}
export interface FrameMsg {
  id: string; seq: number; step: number; t: number; playing: boolean; speed: number; diverged: boolean
  metrics: Record<string, number>; lens: string; grid?: number[]; lo?: number; hi?: number; b64?: string
}

function token(): string | null {
  try {
    const q = new URLSearchParams(location.search).get('token')
    if (q) sessionStorage.setItem('lab-token', q)
    return q || sessionStorage.getItem('lab-token')
  } catch {
    return null
  }
}

export function withToken(url: string): string {
  const t = token()
  return t ? url + (url.includes('?') ? '&' : '?') + 'token=' + encodeURIComponent(t) : url
}

export async function api<T>(path: string, init?: { method?: string; body?: unknown }): Promise<T> {
  const r = await fetch(withToken('/api/' + path), {
    method: init?.method ?? 'GET',
    headers: init?.body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: init?.body !== undefined ? JSON.stringify(init.body) : undefined,
  })
  const d = await r.json().catch(() => null)
  if (!r.ok || d === null) throw new Error(d?.error || `HTTP ${r.status}`)
  return d as T
}

/** Resolves true only when a lab server answers (the Cloudflare build has none). */
export async function labAvailable(): Promise<boolean> {
  try {
    const ctl = new AbortController()
    const timer = setTimeout(() => ctl.abort(), 1500)
    const r = await fetch(withToken('/api/health'), { signal: ctl.signal })
    clearTimeout(timer)
    return r.ok && (await r.json()).ok === true
  } catch {
    return false
  }
}

/** The goal selected in the Goal tab; universes and branches made meanwhile are attached to it. */
let activeGoalId: string | null = null
export function setActiveGoalId(id: string | null) { activeGoalId = id }
export function getActiveGoalId() { return activeGoalId }

export const lab = {
  whites: () => api<{ whites: WhiteSpec[] }>('whites').then((d) => d.whites),
  universes: () => api<{ universes: UniverseInfo[] }>('universes').then((d) => d.universes),
  create: (white: string, seed: number, knobs: Record<string, number>, goal?: string | null) =>
    api<UniverseInfo>('universes', { method: 'POST', body: { white, seed, knobs, goal } }),
  control: (id: string, action: 'play' | 'pause' | 'step' | 'speed', extra: Record<string, number> = {}) =>
    api<UniverseInfo>(`universes/${id}/control`, { method: 'POST', body: { action, ...extra } }),
  set: (id: string, values: Record<string, number>) =>
    api<{ event: LabEvent; universe: UniverseInfo }>(`universes/${id}/set`, { method: 'POST', body: { values } }),
  perturb: (id: string, name: string, args: Record<string, number>) =>
    api<{ event: LabEvent; universe: UniverseInfo }>(`universes/${id}/perturb`, { method: 'POST', body: { name, args } }),
  branch: (id: string, body: { set?: Record<string, number>; perturb?: { name: string; args: Record<string, number> }; goal?: string | null }) =>
    api<UniverseInfo>(`universes/${id}/branch`, { method: 'POST', body: { ...body, goal: activeGoalId } }),
  remove: (id: string) => api<{ ok: boolean }>(`universes/${id}`, { method: 'DELETE' }),
}
