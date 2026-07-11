export interface RoomRun {
  seed: number
  grid: number[]
  reached_level: number | null
  checksum: string
}

export interface Room {
  room_id: string
  title: string
  official: boolean
  kind: string
  parent_room: string | null
  genesis_model?: string
  dimension?: string
  reached_level?: number | null
  candidate_level?: number | null
  physics_status: Record<string, string>
  dimension_status: Record<string, string>
  measured_by?: Record<string, number>
  put_in?: string
  emerged?: string
  frames_ref?: string | null
  render_manifest?: string | null
  lenses?: string[]
  runs?: RoomRun[]
}

export interface Catalog {
  catalog_version: number
  rooms: Room[]
  evidence_library?: { count: number; role_counts: Record<string, number> }
  ai_candidates?: unknown[]
  candidate_rooms?: unknown[]
}

export interface LensDoc {
  source: string
  unit: string
  transform: string
  cyclic: boolean
  geometry: 'plane' | 'volume'
  vmin: number
  vmax: number
  quant: string
  data_b64: string
}

export interface FieldDoc {
  schema_version: number
  dimension: 2 | 3
  grid: number[]
  nframes: number
  times: number[]
  downsample: string
  lenses: Record<string, LensDoc>
  honesty: {
    decorative_particles: boolean
    interpolated_for_display: boolean
    changes_physics: boolean
    quantized_uint8: boolean
  }
}

export interface ManifestLens {
  lens: string
  source: { field: string; unit: string }
  mapping: { transform: string; cyclic?: boolean; clipping: string }
  geometry: 'plane' | 'volume'
  honesty: { decorative_particles: boolean; interpolated_for_display: boolean; changes_physics: boolean }
}

export interface RenderManifest {
  room_id: string
  frames_ref: string
  dimension: 2 | 3
  lenses: ManifestLens[]
  data_source: string
  separated_from_physics_data: boolean
}

/** Decoded lens: quantized uint8 restored to physical values, per frame. */
export interface DecodedLens {
  name: string
  grid: number[]
  nframes: number
  cyclic: boolean
  vmin: number
  vmax: number
  unit: string
  source: string
  /** normalized [0,1] value at (frame,index); index runs over the flattened grid */
  norm: Float32Array // length nframes * prod(grid)
}
