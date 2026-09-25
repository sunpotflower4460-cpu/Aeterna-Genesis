import { useMemo, useState } from 'react'
import type { Sample } from './live'
import type { UniverseInfo } from './api'

// One small chart per measured quantity, one line per universe. Colours follow the universe's letter
// (fixed order A,B,C,D; validated for CVD on the panel surface) and every line is also labelled with its
// letter, so identity is never colour alone. Values are what tools/lab/measure produced -- no smoothing.

export const SERIES = ['#3987e5', '#d95926', '#199e70', '#c98500']
export const OTHER = '#8496ae'
export function seriesColor(label: string): string {
  const i = 'ABCD'.indexOf(label)
  return i >= 0 ? SERIES[i] : OTHER
}

const W = 300, H = 74, PAD_L = 4, PAD_R = 18, PAD_T = 6, PAD_B = 14

function fmt(v: number): string {
  if (!Number.isFinite(v)) return '–'
  const a = Math.abs(v)
  return a >= 1000 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : a >= 0.1 ? v.toFixed(3) : v.toPrecision(2)
}

function Spark({ metric, universes, history }: { metric: string; universes: UniverseInfo[]; history: Map<string, Sample[]> }) {
  const [hover, setHover] = useState<number | null>(null)
  const series = universes
    .map((u) => ({ u, pts: (history.get(u.id) ?? []).filter((s) => typeof s.metrics[metric] === 'number' && Number.isFinite(s.metrics[metric])) }))
    .filter((s) => s.pts.length > 0)
  const all = series.flatMap((s) => s.pts)
  if (!all.length) return null
  const t0 = Math.min(...all.map((p) => p.t)), t1 = Math.max(...all.map((p) => p.t))
  const v = all.map((p) => p.metrics[metric])
  let lo = Math.min(...v), hi = Math.max(...v)
  if (hi - lo < 1e-12) { lo -= 0.5; hi += 0.5 }
  const x = (t: number) => PAD_L + ((t - t0) / (t1 - t0 || 1)) * (W - PAD_L - PAD_R)
  const y = (val: number) => PAD_T + (1 - (val - lo) / (hi - lo)) * (H - PAD_T - PAD_B)
  const tAt = hover === null ? null : t0 + ((hover - PAD_L) / (W - PAD_L - PAD_R)) * (t1 - t0)
  const nearest = (pts: Sample[], t: number) => pts.reduce((b, p) => (Math.abs(p.t - t) < Math.abs(b.t - t) ? p : b), pts[0])

  return (
    <div className="lab-spark">
      <div className="lab-spark-head">
        <span className="mono">{metric}</span>
        <span className="mono muted">{tAt === null ? `${fmt(lo)} – ${fmt(hi)}` : `t=${tAt.toFixed(1)}`}</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`${metric} の時間変化`}
        onMouseMove={(e) => {
          const r = (e.currentTarget as SVGSVGElement).getBoundingClientRect()
          setHover(Math.min(Math.max(((e.clientX - r.left) / r.width) * W, PAD_L), W - PAD_R))
        }}
        onMouseLeave={() => setHover(null)}>
        <line x1={PAD_L} x2={W - PAD_R} y1={H - PAD_B} y2={H - PAD_B} stroke="var(--line-2)" strokeWidth={1} />
        {series.map(({ u, pts }) => {
          const d = pts.map((p, i) => `${i ? 'L' : 'M'}${x(p.t).toFixed(1)},${y(p.metrics[metric]).toFixed(1)}`).join('')
          const last = pts[pts.length - 1]
          return (
            <g key={u.id}>
              <path d={d} fill="none" stroke={seriesColor(u.label)} strokeWidth={2} strokeLinejoin="round" />
              <text x={Math.min(x(last.t) + 4, W - 10)} y={y(last.metrics[metric]) + 4} fontSize={10}
                fill="var(--ink)" className="mono">{u.label}</text>
            </g>
          )
        })}
        {hover !== null && tAt !== null && (
          <g>
            <line x1={hover} x2={hover} y1={PAD_T} y2={H - PAD_B} stroke="var(--muted)" strokeWidth={1} />
            {series.map(({ u, pts }) => {
              const p = nearest(pts, tAt)
              return <circle key={u.id} cx={x(p.t)} cy={y(p.metrics[metric])} r={4} fill={seriesColor(u.label)}
                stroke="var(--panel-solid)" strokeWidth={2} />
            })}
          </g>
        )}
        <text x={PAD_L} y={H - 2} fontSize={9} fill="var(--muted)" className="mono">t={fmt(t0)}</text>
        <text x={W - PAD_R} y={H - 2} fontSize={9} fill="var(--muted)" textAnchor="end" className="mono">{fmt(t1)}</text>
      </svg>
      {tAt !== null && (
        <div className="lab-spark-tip mono">
          {series.map(({ u, pts }) => (
            <span key={u.id}><i style={{ background: seriesColor(u.label) }} />{u.label} {fmt(nearest(pts, tAt).metrics[metric])}</span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ComparePanel({ universes, history, tick }: {
  universes: UniverseInfo[]; history: Map<string, Sample[]>; tick: number
}) {
  // One group per white: time units and the meaning of a metric differ between whites, so universes of
  // different whites are never drawn on the same axes.
  const groups = useMemo(() => {
    const out: { white: string; members: UniverseInfo[]; metrics: string[] }[] = []
    for (const u of universes) {
      let g = out.find((x) => x.white === u.white)
      if (!g) out.push((g = { white: u.white, members: [], metrics: [] }))
      g.members.push(u)
      for (const s of (history.get(u.id) ?? []).slice(-1)) {
        for (const k of Object.keys(s.metrics)) if (!g.metrics.includes(k)) g.metrics.push(k)
      }
    }
    return out
  }, [universes, history, tick])
  if (!universes.length) return <p className="muted">宇宙がまだありません。</p>
  return (
    <div>
      <div className="lab-legend">
        {universes.map((u) => (
          <span key={u.id}><i style={{ background: seriesColor(u.label) }} />{u.label} · {u.white}</span>
        ))}
      </div>
      {groups.map((g) => (
        <section key={g.white} className="lab-group">
          <div className="eyebrow">{g.white} · {g.members.map((u) => u.label).join(', ')}</div>
          {g.metrics.map((m) => <Spark key={m} metric={m} universes={g.members} history={history} />)}
        </section>
      ))}
      <p className="muted lab-note">測定値そのもの（tools/lab・genesis/diagnostics）。縦軸は各グラフで自動。白ごとに分けて描く（時間の単位も量の意味も白ごとに違うため）。この画面を開いてからの記録だけを描く。</p>
    </div>
  )
}
