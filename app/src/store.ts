import { create } from 'zustand'
import type { Catalog, Room, CandidateRoom } from './lib/types'

/** Present a non-official candidate room through the same Room shape the workspace/viewport expect. */
export function candidateAsRoom(c: CandidateRoom): Room {
  return {
    room_id: c.room_id, title: c.title, official: false, kind: 'candidate_room',
    parent_room: c.parent_room, genesis_model: c.genesis_model,
    reached_level: c.reached_level, candidate_level: c.candidate_level,
    physics_status: c.physics_status || {}, dimension_status: c.dimension_status || {},
    frames_ref: c.frames_ref, render_manifest: c.render_manifest, lenses: c.lenses,
  }
}

export type InspectorTab = 'template' | 'genesis' | 'view' | 'physics'

export interface ViewSettings {
  threshold: number // isosurface / cutoff [0,1]
  opacity: number   // [0,1]
  glow: number      // [0,1]
  quality: number   // point budget scale [0.3,1]
}

interface State {
  catalog: Catalog | null
  view: 'lobby' | 'room' | 'compare'
  roomId: string | null
  compareIds: [string, string]
  lens: string | null
  frame: number
  playing: boolean
  speed: number
  inspectorOpen: boolean
  inspectorTab: InspectorTab
  physicsTier: 1 | 2 | 3
  viewSettings: ViewSettings
  pendingGenesis: Record<string, number> | null // View-vs-Genesis separation: staged, not applied

  setCatalog: (c: Catalog) => void
  openRoom: (id: string) => void
  toLobby: () => void
  toCompare: (a: string, b: string) => void
  setCompareId: (slot: 0 | 1, id: string) => void
  setLens: (l: string) => void
  setFrame: (f: number) => void
  togglePlay: () => void
  setSpeed: (s: number) => void
  toggleInspector: () => void
  setTab: (t: InspectorTab) => void
  setPhysicsTier: (n: 1 | 2 | 3) => void
  setView: (patch: Partial<ViewSettings>) => void
  stageGenesis: (key: string, value: number) => void
  discardGenesis: () => void
  currentRoom: () => Room | null
}

export const useStore = create<State>((set, get) => ({
  catalog: null,
  view: 'lobby',
  roomId: null,
  compareIds: ['', ''],
  lens: null,
  frame: 0,
  playing: true,
  speed: 1,
  inspectorOpen: false,
  inspectorTab: 'view',
  physicsTier: 1,
  viewSettings: { threshold: 0.35, opacity: 0.85, glow: 0.6, quality: 1 },
  pendingGenesis: null,

  setCatalog: (c) => set({ catalog: c }),
  openRoom: (id) => set({ view: 'room', roomId: id, frame: 0, playing: true, lens: null, pendingGenesis: null }),
  toLobby: () => set({ view: 'lobby', roomId: null }),
  toCompare: (a, b) => set({ view: 'compare', compareIds: [a, b], frame: 0, playing: true, lens: null }),
  setCompareId: (slot, id) => set((s) => {
    const c: [string, string] = [...s.compareIds]
    c[slot] = id
    return { compareIds: c }
  }),
  setLens: (l) => set({ lens: l }),
  setFrame: (f) => set({ frame: f }),
  togglePlay: () => set((s) => ({ playing: !s.playing })),
  setSpeed: (s2) => set({ speed: s2 }),
  toggleInspector: () => set((s) => ({ inspectorOpen: !s.inspectorOpen })),
  setTab: (t) => set({ inspectorTab: t, inspectorOpen: true }),
  setPhysicsTier: (n) => set({ physicsTier: n }),
  setView: (patch) => set((s) => ({ viewSettings: { ...s.viewSettings, ...patch } })),
  stageGenesis: (key, value) => set((s) => ({ pendingGenesis: { ...(s.pendingGenesis || {}), [key]: value } })),
  discardGenesis: () => set({ pendingGenesis: null }),
  currentRoom: () => {
    const { catalog, roomId } = get()
    if (!catalog || !roomId) return null
    const official = catalog.rooms.find((r) => r.room_id === roomId)
    if (official) return official
    const cand = (catalog.candidate_rooms || []).find((c) => c.room_id === roomId)
    return cand ? candidateAsRoom(cand) : null
  },
}))
