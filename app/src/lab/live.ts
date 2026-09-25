// Live frames from the lab server -> FrameSources the aquarium tanks already know how to draw.
// A live source holds only the last two frames; the tank blends from the previous to the newest one over
// the measured arrival interval, so the picture lags one frame behind the simulation and moves smoothly.

import { useEffect, useMemo, useRef, useState } from 'react'
import type { FrameSource } from '../aquarium/types'
import { withToken, type FrameMsg } from './api'

interface Slot { seq: number; data: Uint8Array; lo: number; hi: number; at: number }

function b64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out
}

export class LiveSource implements FrameSource {
  grid: number[] = []
  private slots: Slot[] = []
  /** 'fixed' maps every frame onto the lens' fixed range (comparable over time and across universes);
   *  'frame' stretches each frame over its own min..max (shows faint late contrast). Display only. */
  mode: 'fixed' | 'frame' = 'fixed'
  constructor(public vmin: number, public vmax: number, public cyclic: boolean, grid: number[]) { this.grid = grid }

  get count() { return this.slots.length }
  key(i: number) { return this.slots[i]?.seq ?? -1 }
  data(i: number) { return this.slots[i].data }
  affine(i: number): [number, number] {
    const s = this.slots[i]
    if (!s || this.cyclic || this.mode === 'frame') return [1, 0]
    const span = this.vmax - this.vmin || 1
    return [(s.hi - s.lo) / span, (s.lo - this.vmin) / span]
  }

  push(m: FrameMsg) {
    if (m.diverged || !m.grid || m.b64 === undefined) return
    if (this.slots.length && this.slots[this.slots.length - 1].seq === m.seq) return
    if (m.grid.join('x') !== this.grid.join('x')) return   // the tank's textures are sized for this.grid
    this.slots.push({ seq: m.seq, data: b64ToBytes(m.b64), lo: m.lo ?? 0, hi: m.hi ?? 1, at: performance.now() })
    if (this.slots.length > 2) this.slots.shift()
  }

  /** Continuous position in [0, count-1] for the tank clock. */
  position(now: number): number {
    if (this.slots.length < 2) return 0
    const [a, b] = this.slots
    const interval = Math.min(Math.max(b.at - a.at, 40), 600)
    return Math.min(1, (now - b.at) / interval)
  }
}

export interface Sample { seq: number; t: number; step: number; metrics: Record<string, number> }
export interface LiveState { step: number; t: number; playing: boolean; speed: number; diverged: boolean; metrics: Record<string, number> }

const HISTORY = 480

/** Subscribe to the frames of the given universes (each with its chosen lens). */
export function useLabStream(subs: { id: string; lens: string; vmin: number; vmax: number; cyclic: boolean; grid: number[] }[],
  onRoster: () => void) {
  const key = subs.map((s) => `${s.id}:${s.lens}`).join(',')
  const sources = useRef(new Map<string, LiveSource>())
  const history = useRef(new Map<string, Sample[]>())
  const [live, setLive] = useState<Record<string, LiveState>>({})
  const pending = useRef<Record<string, LiveState>>({})
  const rosterCb = useRef(onRoster)
  rosterCb.current = onRoster

  // one source per universe+lens; switching lens gives a fresh source (grid / range may differ)
  const map = useMemo(() => {
    const next = new Map<string, LiveSource>()
    for (const s of subs) {
      const k = `${s.id}:${s.lens}`
      next.set(s.id, sources.current.get(k) ?? new LiveSource(s.vmin, s.vmax, s.cyclic, s.grid))
    }
    sources.current = new Map(subs.map((s) => [`${s.id}:${s.lens}`, next.get(s.id)!]))
    return next
  }, [key]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const es = new EventSource(withToken('/api/stream?u=' + encodeURIComponent(key)))
    es.addEventListener('frame', (ev) => {
      const m = JSON.parse((ev as MessageEvent).data) as FrameMsg
      map.get(m.id)?.push(m)
      const h = history.current.get(m.id) ?? []
      // keyed by frame sequence, not step: a perturbation changes the state without advancing the step
      if (!m.diverged && (!h.length || h[h.length - 1].seq !== m.seq)) {
        h.push({ seq: m.seq, t: m.t, step: m.step, metrics: m.metrics })
        if (h.length > HISTORY) h.splice(0, h.length - HISTORY)
        history.current.set(m.id, h)
      }
      pending.current[m.id] = { step: m.step, t: m.t, playing: m.playing, speed: m.speed, diverged: m.diverged,
        ...(m.diverged ? {} : { metrics: m.metrics }) } as LiveState
    })
    es.addEventListener('universes', () => rosterCb.current())
    const timer = setInterval(() => {
      if (Object.keys(pending.current).length) {
        const p = pending.current
        pending.current = {}
        setLive((old) => ({ ...old, ...p }))
      }
    }, 250)
    return () => { es.close(); clearInterval(timer) }
  }, [key, map])

  return { sources: map, history: history.current, live }
}
