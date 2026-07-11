import type { Room } from '../lib/types'

export function dimBadge(room: Room) {
  const d = room.dimension || ''
  if (d === 'full-3d') return <span className="badge b-official">Official 3D</span>
  if (d === '2d') return <span className="badge b-2d">2D · Validated</span>
  return <span className="badge">{d || 'room'}</span>
}

export function physicsBadge(room: Room) {
  const allPass = Object.values(room.physics_status || {}).every((v) => v === 'passed')
  return <span className={'badge ' + (allPass ? 'b-official' : 'b-warn')}>{allPass ? 'Physics Verified' : 'Needs Review'}</span>
}

export function LevelChip({ room }: { room: Room }) {
  return (
    <span className="badge">Level {room.reached_level ?? '?'}
      {room.candidate_level ? <span className="muted"> · cand {room.candidate_level}</span> : null}</span>
  )
}

export const LEVEL_TEXT: Record<number, string> = {
  0: '未分化な始原状態',
  1: '差・模様が自然形成',
  2: '局在構造が自然形成',
  3: '自発運動・循環',
  4: '持続する全体性',
  5: '機能の共分化',
}
