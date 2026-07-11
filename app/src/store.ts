import { create } from 'zustand'
import type { Catalog, Room } from './lib/types'

export type InspectorTab = 'template' | 'genesis' | 'view' | 'physics'

export interface ViewSettings {
  threshold: number // isosurface / cutoff [0,1]
  opacity: number   // [0,1]
  glow: number      // [0,1]
  quality: number   // point budget scale [0.3,1]
}

interface State {
  catalog: Catalog | null
  view: 'lobby' | 'room'
  roomId: string | null
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
    return catalog?.rooms.find((r) => r.room_id === roomId) || null
  },
}))
