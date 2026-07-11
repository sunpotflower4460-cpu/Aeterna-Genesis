import { useEffect, useState } from 'react'
import { loadField, loadManifest, decodeLens } from './data'
import type { FieldDoc, RenderManifest, DecodedLens } from './types'

export interface RoomData {
  field: FieldDoc | null
  manifest: RenderManifest | null
  lenses: Record<string, DecodedLens>
  lensNames: string[]
  loading: boolean
  error: string | null
}

export function useRoomField(roomId: string | null): RoomData {
  const [data, setData] = useState<RoomData>({
    field: null, manifest: null, lenses: {}, lensNames: [], loading: true, error: null,
  })

  useEffect(() => {
    let alive = true
    if (!roomId) return
    setData((d) => ({ ...d, loading: true, error: null }))
    Promise.all([loadField(roomId), loadManifest(roomId)])
      .then(([field, manifest]) => {
        if (!alive) return
        if (!field) {
          setData({ field: null, manifest, lenses: {}, lensNames: [], loading: false, error: 'no recorded fields' })
          return
        }
        const lenses: Record<string, DecodedLens> = {}
        for (const name of Object.keys(field.lenses)) {
          lenses[name] = decodeLens(name, field.lenses[name], field.grid, field.nframes)
        }
        setData({ field, manifest, lenses, lensNames: Object.keys(field.lenses), loading: false, error: null })
      })
      .catch((e) => alive && setData({ field: null, manifest: null, lenses: {}, lensNames: [], loading: false, error: String(e) }))
    return () => { alive = false }
  }, [roomId])

  return data
}
