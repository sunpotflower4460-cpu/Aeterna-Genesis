import { useEffect, useState } from 'react'
import {
  loadDreamReport,
  loadViewPresets,
  type DreamEvent,
  type DreamReport,
  type ViewPreset,
} from '../lib/dream'
import { useStore } from '../store'

const KIND: Record<string, { label: string; glyph: string }> = {
  NEW_BEHAVIOR: { label: '新規候補', glyph: '✨' },
  NEW_REGION: { label: '新規領域', glyph: '◇' },
  REPRODUCED: { label: '再現成功', glyph: '↻' },
  PROMOTION_READY: { label: '昇格候補', glyph: '▲' },
  STAGE_PROMOTED: { label: '段階通過', glyph: '✓' },
  DIMENSION_FAILURE: { label: '3D移行失敗', glyph: '▽' },
  NEGATIVE_RESULT: { label: '負の結果', glyph: '−' },
  NUMERICAL_WARNING: { label: '数値警告', glyph: '!' },
  RARE_EVENT: { label: '希少挙動', glyph: '✦' },
}

function Count({ value, label }: { value: number; label: string }) {
  return (
    <div style={{ minWidth: 92 }}>
      <div className="mono" style={{ fontSize: 19, color: 'var(--ink)' }}>{value}</div>
      <div className="mono muted" style={{ fontSize: 10.5 }}>{label}</div>
    </div>
  )
}

function EventCard({ event, preset }: { event: DreamEvent; preset?: ViewPreset }) {
  const openRoom = useStore((s) => s.openRoom)
  const toCompare = useStore((s) => s.toCompare)
  const setLens = useStore((s) => s.setLens)
  const setSpeed = useStore((s) => s.setSpeed)
  const setView = useStore((s) => s.setView)
  const setFrame = useStore((s) => s.setFrame)
  const catalog = useStore((s) => s.catalog)!
  const info = KIND[event.kind] || { label: event.kind, glyph: '•' }
  const roomExists = !!event.room_id && (
    catalog.rooms.some((r) => r.room_id === event.room_id) ||
    (catalog.candidate_rooms || []).some((r) => r.room_id === event.room_id)
  )
  const parentExists = !!event.parent_room && catalog.rooms.some((r) => r.room_id === event.parent_room)
  const canCompare = roomExists && parentExists

  const applyPreset = () => {
    if (!preset) return
    setLens(preset.lens)
    setSpeed(preset.playback.speed)
    setFrame(0)
    setView({
      threshold: preset.view.threshold,
      opacity: preset.view.opacity,
      glow: preset.view.glow,
      quality: preset.view.quality,
    })
  }
  const observe = () => {
    if (!event.room_id) return
    openRoom(event.room_id)
    applyPreset()
  }
  const compare = () => {
    if (!event.parent_room || !event.room_id) return
    toCompare(event.parent_room, event.room_id)
    applyPreset()
  }

  return (
    <div style={{ padding: '11px 0', borderTop: '1px solid var(--line)', display: 'grid', gap: 6 }}>
      <div style={{ display: 'flex', gap: 7, alignItems: 'center', flexWrap: 'wrap' }}>
        <span>{info.glyph}</span>
        <span className="badge" style={{ color: event.kind === 'PROMOTION_READY' ? 'var(--official)' : 'var(--accent)' }}>
          {info.label}
        </span>
        <span style={{ fontSize: 13.5, fontWeight: 600 }}>{event.title}</span>
        <span style={{ flex: 1 }} />
        <span className="mono muted" style={{ fontSize: 10 }}>見る価値 {event.visual_interest}</span>
      </div>
      <div style={{ fontSize: 12.5, lineHeight: 1.65, color: 'var(--ink)' }}>{event.plain}</div>
      <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.55 }}>{event.why}</div>
      {(roomExists || canCompare) && (
        <div style={{ display: 'flex', gap: 7, marginTop: 2, flexWrap: 'wrap' }}>
          {roomExists && (
            <button className="lens" onClick={observe}>
              👁 見る{preset ? `（${preset.lens} Preset）` : ''}
            </button>
          )}
          {canCompare && (
            <button className="lens" onClick={compare}>
              親と比較{preset ? '（同期Preset）' : ''}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default function DreamNightReport() {
  const [report, setReport] = useState<DreamReport | null | undefined>(undefined)
  const [presets, setPresets] = useState<Record<string, ViewPreset>>({})
  useEffect(() => {
    Promise.all([loadDreamReport(), loadViewPresets()])
      .then(([r, ps]) => {
        setReport(r)
        setPresets(Object.fromEntries(ps.map((p) => [p.preset_id, p])))
      })
      .catch(() => setReport(null))
  }, [])

  if (report === undefined) return null
  if (!report) {
    return (
      <div className="glass" style={{ padding: 14, marginBottom: 18, border: '1px solid var(--line)', background: 'var(--panel)' }}>
        <div className="mono muted" style={{ fontSize: 11 }}>🌙 Night Report はまだありません。Dream Loop 実行後にここへ届きます。</div>
      </div>
    )
  }
  const c = report.counts
  const top = report.events.slice(0, 6)
  return (
    <section className="glass" style={{ padding: 16, marginBottom: 22, border: '1px solid rgba(79,227,224,.24)', background: 'var(--panel)' }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'baseline', flexWrap: 'wrap' }}>
        <span style={{ fontSize: 18 }}>🌙</span>
        <div>
          <div className="eyebrow" style={{ marginBottom: 3 }}>Genesis Night Report</div>
          <div style={{ fontWeight: 650, fontSize: 16 }}>何もしていない時間に起きたこと</div>
        </div>
        <span style={{ flex: 1 }} />
        <span className="mono muted" style={{ fontSize: 10.5 }}>
          {new Date(report.generated_at).toLocaleString('ja-JP')} · {report.burst_id}
        </span>
      </div>

      <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', margin: '15px 0 9px' }}>
        <Count value={c.experiments} label="実験 / job" />
        <Count value={c.new_behavior} label="新規候補" />
        <Count value={c.reproduced} label="再現成功" />
        <Count value={c.promotion_ready} label="昇格候補" />
        <Count value={c.dimension_failure} label="3Dで崩壊" />
      </div>

      {report.headline && (
        <div style={{ padding: '11px 12px', margin: '10px 0 3px', borderRadius: 10, background: 'var(--accent-dim)' }}>
          <div className="mono" style={{ fontSize: 10.5, color: 'var(--accent)', marginBottom: 4 }}>MOST INTERESTING</div>
          <div style={{ fontSize: 14, fontWeight: 650, marginBottom: 4 }}>{report.headline.title}</div>
          <div style={{ fontSize: 12.5, lineHeight: 1.65 }}>{report.headline.plain}</div>
        </div>
      )}

      {top.map((e) => (
        <EventCard key={e.event_id} event={e} preset={e.view_preset_id ? presets[e.view_preset_id] : undefined} />
      ))}
      <div className="mono muted" style={{ fontSize: 10.5, marginTop: 8, lineHeight: 1.55 }}>
        novelty / 見る価値は観察・ランキング用。Preset は表示だけを変え、成功判定や official 昇格には使用しません。
      </div>
    </section>
  )
}
