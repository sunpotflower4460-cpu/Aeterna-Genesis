// Aquarium templates: short t=0 replays of whites, chosen because something visibly grows.
// Data contract = the same field.json the Observatory already reads (uint8 frames, stored vmin/vmax,
// honesty flags), plus one entry per template in app/public/aquarium/templates.json.

export type Transfer = 'high' | 'low' | 'cyclic' | 'diverging'

export interface TemplateLens {
  name: string            // key in field.json lenses
  label: string           // short human label (ja)
  transfer: Transfer      // how the tank maps values to light (display only)
}

export interface AquariumTemplate {
  id: string
  title: string           // ja
  white: string           // model / law family
  dimension: 2 | 3
  caption: string         // plain-language (ja): what you are looking at
  put_in: string[]        // what the start condition PLACED
  emerged: string[]       // what GREW from t=0
  level: string           // measured level / status, e.g. "L3" or "frontier"
  tier: string            // claim tier
  source: string          // experiment / room / model the recipe follows
  recipe: Record<string, unknown>  // seed, grid, steps, params (reproducible)
  lenses: TemplateLens[]
  default_lens: string
}

export interface TankLens {
  name: string
  grid: number[]
  nframes: number
  vmin: number
  vmax: number
  unit: string
  cyclic: boolean
  frames: Uint8Array      // nframes * prod(grid), C order (slowest axis first)
}

export interface TankField {
  dimension: 2 | 3
  grid: number[]
  nframes: number
  times: number[]
  lenses: Record<string, TankLens>
}
