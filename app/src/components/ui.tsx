import type { Room } from '../lib/types'

export function dimBadge(room: Room) {
  const d = room.dimension || ''
  if (d === 'full-3d') return <span className="badge b-official">Official 3D</span>
  if (d === '2d') return <span className="badge b-2d">2D · Validated</span>
  return <span className="badge">{d || 'room'}</span>
}

export function candidateBadge() {
  return <span className="badge b-warn" title="非公式・自己昇格しない候補">候補 · 非公式</span>
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

// plain-Japanese labels for lens toggle buttons (English name stays as the id)
export const LENS_JP: Record<string, string> = {
  phase: '位相', density: '密度', temperature: '温度', velocity: '流速',
  vorticity: '渦度', composition: '組成', boundary: '界面',
}

// honest, plain-language legend for what the colors mean in the current lens.
// NOTE: the vortex LINES are where the condensate is depleted (低密度の芯) — the render
// lights those cores up, so "明るい筋 = 渦線" in both phase and density views.
export const LENS_LEGEND: Record<string, string> = {
  phase: '色 = 位相（場の回り方）。明るい筋 = 渦線（構造）／暗い = 一様な海',
  density: '明るい筋 = 渦線（密度が薄い芯）／暗い = 密度が高い凝縮体',
  temperature: '暖色ほど高温・寒色ほど低温',
  velocity: '明るいほど流れが速い',
  vorticity: '明るいほど渦が強い',
  composition: '色の違い = 二相の組成',
  boundary: '明るいほど界面（相の境目）',
}
