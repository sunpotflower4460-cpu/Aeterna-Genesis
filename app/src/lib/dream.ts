const BASE = import.meta.env.BASE_URL + 'data/dream/'

export type DreamEventKind =
  | 'NEW_BEHAVIOR'
  | 'NEW_REGION'
  | 'REPRODUCED'
  | 'PROMOTION_READY'
  | 'STAGE_PROMOTED'
  | 'DIMENSION_FAILURE'
  | 'NEGATIVE_RESULT'
  | 'NUMERICAL_WARNING'
  | 'RARE_EVENT'

export interface DreamEvent {
  event_id: string
  kind: DreamEventKind
  source: string
  source_key: string
  title: string
  plain: string
  why: string
  facts: Record<string, unknown>
  scientific_status: string
  visual_interest: 'low' | 'medium' | 'high' | string
  room_id: string | null
  parent_room: string | null
  view_preset_id: string | null
}

export interface HumanResearchSummary {
  version: number
  purpose: string
  destination: string
  current_position: string
  achieved_this_time: string[]
  not_achieved_yet: string[]
  next_questions: string[]
  reading_note: string
  technical_details_preserved_elsewhere: boolean
}

export interface DreamReport {
  report_version: number
  burst_id: string
  generated_at: string
  counts: {
    experiments: number
    expanded_trials: number
    native_jobs: number
    new_behavior: number
    reproduced: number
    promotion_ready: number
    stage_promoted: number
    dimension_failure: number
    negative_result: number
    rare_event: number
    numerical_warning: number
    new_region: number
  }
  headline_event_id: string | null
  headline: DreamEvent | null
  events: DreamEvent[]
  honesty: Record<string, boolean>
  human_summary?: HumanResearchSummary
}

export interface ViewPreset {
  preset_version: number
  preset_id: string
  event_id: string
  room_id: string | null
  parent_room: string | null
  ready: boolean
  lens: string
  playback: { speed: number; start_fraction: number; end_fraction: number; loop: boolean }
  view: { threshold: number; opacity: number; glow: number; quality: number }
  comparison: { mode: string; sync_time: boolean }
  reason: string
}

async function loadOptional<T>(name: string): Promise<T | null> {
  const r = await fetch(BASE + name)
  if (!r.ok) return null
  return r.json()
}

export function loadDreamReport(): Promise<DreamReport | null> {
  return loadOptional<DreamReport>('latest.json')
}

export async function loadViewPresets(): Promise<ViewPreset[]> {
  const doc = await loadOptional<{ presets?: ViewPreset[] }>('view-presets.json')
  return doc?.presets || []
}
