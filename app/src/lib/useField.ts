import { useEffect, useRef, useState } from 'react'
import type { FieldDoc, RenderManifest, DecodedLens } from './types'

export interface RoomData {
  field: FieldDoc | null
  manifest: RenderManifest | null
  lenses: Record<string, DecodedLens>
  lensNames: string[]
  loading: boolean
  error: string | null
}

// absolute so the Web Worker's fetch resolves against the page, not the worker script location
const BASE = new URL(import.meta.env.BASE_URL + 'data/', location.href).href
const EMPTY: RoomData = { field: null, manifest: null, lenses: {}, lensNames: [], loading: true, error: null }

// Decode recorded fields off the UI thread (Web Worker). Falls back to inline decode if workers are
// unavailable (older embeds).
export function useRoomField(roomId: string | null): RoomData {
  const [data, setData] = useState<RoomData>(EMPTY)
  const workerRef = useRef<Worker | null>(null)

  useEffect(() => {
    try {
      workerRef.current = new Worker(new URL('./decode.worker.ts', import.meta.url), { type: 'module' })
    } catch {
      workerRef.current = null
    }
    return () => workerRef.current?.terminate()
  }, [])

  useEffect(() => {
    let alive = true
    if (!roomId) return
    setData({ ...EMPTY })
    const w = workerRef.current
    if (w) {
      w.onmessage = (e: MessageEvent<any>) => {
        if (!alive || e.data.roomId !== roomId) return
        const { field, manifest, lenses, error } = e.data
        if (error || !field) {
          setData({ field: null, manifest: manifest ?? null, lenses: {}, lensNames: [], loading: false, error: error ?? 'no recorded fields' })
          return
        }
        setData({ field, manifest, lenses, lensNames: Object.keys(lenses), loading: false, error: null })
      }
      w.postMessage({ base: BASE, roomId })
    } else {
      // fallback: main-thread decode
      import('./data').then(async ({ loadField, loadManifest, decodeLens }) => {
        const [field, manifest] = await Promise.all([loadField(roomId), loadManifest(roomId)])
        if (!alive) return
        if (!field) { setData({ field: null, manifest, lenses: {}, lensNames: [], loading: false, error: 'no recorded fields' }); return }
        const lenses: Record<string, DecodedLens> = {}
        for (const n of Object.keys(field.lenses)) lenses[n] = decodeLens(n, field.lenses[n], field.grid, field.nframes)
        setData({ field, manifest, lenses, lensNames: Object.keys(lenses), loading: false, error: null })
      })
    }
    return () => { alive = false }
  }, [roomId])

  return data
}
