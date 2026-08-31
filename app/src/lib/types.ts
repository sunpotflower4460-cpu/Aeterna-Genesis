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

export interface CandidateRoom {
  room_id: string
  title: string
  kind: 'candidate_room'
  official: false
  parent_room: string | null
  genesis_model?: string
  status?: string
  reached_level?: number | null
  candidate_level?: number | null
  dimension_status: Record<string, string>
  physics_status?: Record<string, string>
  render_manifest?: string | null
  frames_ref?: string | null
  lenses?: string[]
  source?: string
  // Discovery Inbox (Phase 4)
  diff_vs_parent?: Record<string, { from: number | null; to: number | null }>
  parent_reached_level?: number | null
  delta_level?: number | null
  promotion?: Promotion
}

export interface PromotionStage {
  name: string
  status: string
}

export interface Promotion {
  stages: PromotionStage[]
  passed: string[]
  current: string
  rejected_in_3d: boolean
  is_official: false
}

export interface Job {
  job_id: string
  parent_room: string | null
  override: { param: string; to: number } | null
  seed: number | null
  status: 'queued' | 'running' | 'done' | 'rejected'
  progress?: number | null
  result_room?: string | null
  reached_level?: number | null
  checksum?: string | null
  measured_by?: Record<string, number>
}

export interface Catalog {
  catalog_version: number
  rooms: Room[]
  evidence_library?: { count: number; role_counts: Record<string, number> }
  ai_candidates?: unknown[]
  candidate_rooms?: CandidateRoom[]
  jobs?: Job[]
}

export type AquariumOrigin = 'human' | 'ai' | 'joint'
export type AquariumStatus = 'idea' | 'planned' | 'active' | 'paused' | 'archived'
export type AquariumIntentMode = 'open_ended' | 'goal_directed'

export interface AquariumIntent {
  mode: AquariumIntentMode
  goal: string
  planning_may_read_goal: true
  physics_may_read_goal: false
}

export interface AquariumIntegrity {
  target_outcome_seeded: boolean
  target_morphology_seeded: boolean
  outcome_location_seeded: boolean
  outcome_time_seeded: boolean
  planning_metadata_changes_physics: false
  scientific_promotion_effect: false
}

export interface Aquarium {
  aquarium_id: string
  title: string
  summary?: string
  origin: AquariumOrigin
  status: AquariumStatus
  intent: AquariumIntent
  classes: string[]
  recipe_space: Record<string, unknown>
  observation_focus: string[]
  related_aquaria?: string[]
  evidence_refs: string[]
  run_refs?: string[]
  integrity: AquariumIntegrity
}

export interface AquariumRegistry {
  version: number
  mode: 'universe-aquarium-registry'
  aquaria: Aquarium[]
  policy: {
    intent_is_scientific_evidence: false
    planning_may_read_intent: true
    physics_may_read_intent_text: false
    goal_directed_equals_target_encoded: false
    seeded_is_lower_value: false
    negative_results_are_preserved: true
  }
}

export type AquariumNoteKind = 'idea' | 'observation' | 'question' | 'direction' | 'decision' | 'warning'

export interface AquariumNote {
  note_id: string
  aquarium_id: string
  author_role: AquariumOrigin
  kind: AquariumNoteKind
  created_at: string
  text: string
  evidence_refs: string[]
  status?: 'open' | 'accepted' | 'superseded' | 'done'
}

export interface AquariumNotebook {
  version: number
  mode: 'universe-aquarium-notebook'
  entries: AquariumNote[]
  policy: {
    notes_are_scientific_evidence: false
    notes_change_physics: false
    history_is_append_only_in_spirit: true
  }
}

export interface AquariumDraft {
  title: string
  intentMode: AquariumIntentMode
  goal: string
  note: string
  createdAt: string
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
