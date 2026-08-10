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
  NEW_BEHAVIOR: { label: '新しく見つかった候補', glyph: '✨' },
  NEW_REGION: { label: '新しく調べた領域', glyph: '◇' },
  REPRODUCED: { label: '繰り返し確認', glyph: '↻' },
  PROMOTION_READY: { label: '次の審査候補', glyph: '▲' },
  STAGE_PROMOTED: { label: '段階通過', glyph: '✓' },
  DIMENSION_FAILURE: { label: '立体条件で崩れた', glyph: '▽' },
  NEGATIVE_RESULT: { label: '予想と違った結果', glyph: '−' },
  NUMERICAL_WARNING: { label: '計算上の注意', glyph: '!' },
  RARE_EVENT: { label: '珍しい変化', glyph: '✦' },
}

function Count({ value, label }: { value: number; label: string }) {
  return (
    <div style={{ minWidth: 108 }}>
      <div className="mono" style={{ fontSize: 19, color: 'var(--ink)' }}>{value}</div>
      <div className="muted" style={{ fontSize: 10.5 }}>{label}</div>
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
        <span className="mono muted" style={{ fontSize: 10 }}>観察優先度 {event.visual_interest}</span>
      </div>
      <div style={{ fontSize: 12.5, lineHeight: 1.65, color: 'var(--ink)' }}>{event.plain}</div>
      <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.55 }}>{event.why}</div>
      {(roomExists || canCompare) && (
        <div style={{ display: 'flex', gap: 7, marginTop: 2, flexWrap: 'wrap' }}>
          {roomExists && (
            <button className="lens" onClick={observe}>
              👁 見る{preset ? '（表示設定を適用）' : ''}
            </button>
          )}
          {canCompare && (
            <button className="lens" onClick={compare}>
              親と比較{preset ? '（表示を同期）' : ''}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

function TextBlock({ title, text }: { title: string; text: string }) {
  return (
    <div style={{ padding: '13px 0', borderTop: '1px solid var(--line)' }}>
      <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6 }}>{title}</div>
      <div style={{ fontSize: 13.5, lineHeight: 1.8 }}>{text}</div>
    </div>
  )
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div style={{ padding: '13px 0', borderTop: '1px solid var(--line)' }}>
      <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 7 }}>{title}</div>
      <div style={{ display: 'grid', gap: 7 }}>
        {items.map((item, index) => (
          <div key={`${title}-${index}`} style={{ display: 'flex', gap: 8, fontSize: 13.5, lineHeight: 1.75 }}>
            <span style={{ color: 'var(--accent)' }}>•</span>
            <span>{item}</span>
          </div>
        ))}
      </div>
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
        <div className="muted" style={{ fontSize: 11 }}>自動研究レポートはまだありません。実験が終わると、ここに届きます。</div>
      </div>
    )
  }

  const c = report.counts
  const top = report.events.slice(0, 6)
  const human = report.human_summary

  return (
    <section className="glass" style={{ padding: 16, marginBottom: 22, border: '1px solid rgba(79,227,224,.24)', background: 'var(--panel)' }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'baseline', flexWrap: 'wrap', marginBottom: 8 }}>
        <span style={{ fontSize: 18 }}>🌱</span>
        <div>
          <div className="eyebrow" style={{ marginBottom: 3 }}>自動研究レポート</div>
          <div style={{ fontWeight: 650, fontSize: 16 }}>目的地と現在地から読む</div>
        </div>
      </div>

      {human ? (
        <>
          <div style={{ padding: '13px 14px', margin: '10px 0 3px', borderRadius: 10, background: 'var(--accent-dim)' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent)', marginBottom: 6 }}>要するに、目的地はどこか</div>
            <div style={{ fontSize: 14, lineHeight: 1.8 }}>{human.destination}</div>
          </div>
          <TextBlock title="現在地はどこか" text={human.current_position} />
          <ListBlock title="今回できたこと" items={human.achieved_this_time} />
          <ListBlock title="まだできていないこと" items={human.not_achieved_yet} />
          <ListBlock title="次に確かめること" items={human.next_questions} />
          <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.7, paddingTop: 10 }}>
            {human.reading_note}
          </div>
        </>
      ) : report.headline ? (
        <div style={{ padding: '11px 12px', margin: '10px 0 3px', borderRadius: 10, background: 'var(--accent-dim)' }}>
          <div style={{ fontSize: 10.5, color: 'var(--accent)', marginBottom: 4 }}>今回もっとも気になったこと</div>
          <div style={{ fontSize: 14, fontWeight: 650, marginBottom: 4 }}>{report.headline.title}</div>
          <div style={{ fontSize: 12.5, lineHeight: 1.65 }}>{report.headline.plain}</div>
        </div>
      ) : null}

      <details style={{ marginTop: 16, borderTop: '1px solid var(--line)', paddingTop: 12 }}>
        <summary style={{ cursor: 'pointer', fontSize: 12.5, fontWeight: 650 }}>詳しい内部記録を見る</summary>
        <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.65, marginTop: 9 }}>
          ここから下は、検証や再現のための細かい記録です。最初に研究の意味を理解するためには読まなくても大丈夫です。
        </div>
        <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', margin: '15px 0 9px' }}>
          <Count value={c.experiments} label="実験の総数" />
          <Count value={c.new_behavior} label="新しく見つかった候補" />
          <Count value={c.reproduced} label="繰り返し確認できたもの" />
          <Count value={c.promotion_ready} label="次の審査に進める候補" />
          <Count value={c.dimension_failure} label="立体条件で崩れたもの" />
        </div>
        <div className="mono muted" style={{ fontSize: 10.5, margin: '8px 0', lineHeight: 1.55 }}>
          記録時刻 {new Date(report.generated_at).toLocaleString('ja-JP')} · 内部識別子 {report.burst_id}
        </div>
        {top.map((e) => (
          <EventCard key={e.event_id} event={e} preset={e.view_preset_id ? presets[e.view_preset_id] : undefined} />
        ))}
        <div className="muted" style={{ fontSize: 10.5, marginTop: 8, lineHeight: 1.55 }}>
          新しさや観察優先度は、見る順番を決めるための補助です。物理的な成功判定や正式な昇格条件そのものではありません。
        </div>
      </details>
    </section>
  )
}
