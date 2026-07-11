import { useStore } from '../store'
import type { CandidateRoom, Job, Promotion } from '../lib/types'
import { candidateBadge } from './ui'

const STAGE_LABEL: Record<string, string> = {
  exploration_2d: '2D screen', local_3d: 'local 3D', coarse_global_3d: 'coarse 3D', full_3d: 'full 3D',
}

function fmtVal(v: number | null | undefined): string {
  if (v == null) return '—'
  if (v !== 0 && (Math.abs(v) < 1e-3 || Math.abs(v) >= 1e4)) return v.toExponential(2)
  return String(Math.round(v * 1e6) / 1e6)
}

function Pipeline({ promotion }: { promotion: Promotion }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
      {promotion.stages.map((s, i) => {
        const passed = s.status === 'passed'
        const isCurrent = s.name === promotion.current && !passed
        const color = passed ? 'var(--official)' : isCurrent ? 'var(--accent)' : 'var(--faint)'
        return (
          <span key={s.name} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            {i > 0 && <span style={{ color: 'var(--faint)', fontSize: 11 }}>›</span>}
            <span className="mono" style={{
              fontSize: 10.5, padding: '3px 7px', borderRadius: 7, color,
              border: `1px solid ${passed ? 'rgba(89,217,139,.35)' : isCurrent ? 'rgba(79,227,224,.4)' : 'var(--line)'}`,
              background: passed ? 'rgba(89,217,139,.08)' : isCurrent ? 'var(--accent-dim)' : 'transparent',
            }}>{passed ? '✓ ' : isCurrent ? '▸ ' : ''}{STAGE_LABEL[s.name] || s.name}</span>
          </span>
        )
      })}
    </div>
  )
}

function DiffTable({ diff }: { diff: Record<string, { from: number | null; to: number | null }> }) {
  const keys = Object.keys(diff)
  if (!keys.length) return <div className="muted mono" style={{ fontSize: 11 }}>親と同一の始原条件（差分なし）</div>
  return (
    <div style={{ display: 'grid', gap: 4 }}>
      {keys.map((k) => (
        <div key={k} className="mono" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11.5 }}>
          <span className="muted" style={{ minWidth: 130 }}>{k}</span>
          <span style={{ color: 'var(--faint)' }}>{fmtVal(diff[k].from)}</span>
          <span style={{ color: 'var(--accent)' }}>→</span>
          <span style={{ color: 'var(--ink)' }}>{fmtVal(diff[k].to)}</span>
        </div>
      ))}
    </div>
  )
}

function DeltaChip({ delta }: { delta: number | null | undefined }) {
  if (delta == null) return null
  const up = delta > 0, flat = delta === 0
  const color = up ? 'var(--official)' : flat ? 'var(--muted)' : 'var(--warn)'
  return (
    <span className="badge" style={{ color }} title="到達 Level の親との差">
      {up ? '▲' : flat ? '＝' : '▼'} 親比 {delta > 0 ? '+' : ''}{delta}
    </span>
  )
}

function DiscoveryCard({ room }: { room: CandidateRoom }) {
  const openRoom = useStore((s) => s.openRoom)
  const hasFields = !!room.frames_ref
  const isLive = room.source === 'candidates' && room.render_manifest  // recorded => Live Runner run
  return (
    <div className="glass" style={{ padding: 16, display: 'grid', gap: 12, border: '1px dashed var(--line)', background: 'var(--panel)' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ fontWeight: 600, fontSize: 15 }}>{room.title}</span>
        {candidateBadge()}
        <span className="badge">{isLive ? 'Live Runner' : 'AI Lab'}</span>
        <span style={{ flex: 1 }} />
        <span className="mono muted" style={{ fontSize: 11 }}>{room.room_id}</span>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <span className="badge">reached L{room.reached_level ?? '?'}</span>
        <span className="mono muted" style={{ fontSize: 11 }}>親 {room.parent_room} (L{room.parent_reached_level ?? '?'})</span>
        <DeltaChip delta={room.delta_level} />
      </div>

      <div style={{ display: 'grid', gap: 6 }}>
        <div className="mono" style={{ fontSize: 10.5, color: 'var(--muted)' }}>始原条件の差（親→この候補）</div>
        <DiffTable diff={room.diff_vs_parent || {}} />
      </div>

      <div style={{ display: 'grid', gap: 6 }}>
        <div className="mono" style={{ fontSize: 10.5, color: 'var(--muted)' }}>昇格パイプライン（自己昇格しない・測定が運んだ所まで）</div>
        {room.promotion && <Pipeline promotion={room.promotion} />}
        {room.promotion?.rejected_in_3d && (
          <div className="mono" style={{ fontSize: 10.5, color: 'var(--warn)' }}>3D で棄却（rejected_in_3d）</div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button className="lens" disabled={!hasFields} style={hasFields
          ? { color: 'var(--accent)', borderColor: 'rgba(79,227,224,.4)' } : { opacity: 0.5 }}
          onClick={() => hasFields && openRoom(room.room_id)}>
          {hasFields ? '▶ 実測場を再生' : '記録場なし（screen のみ）'}
        </button>
        {room.parent_room && (
          <button className="lens" onClick={() => openRoom(room.parent_room!)}>親 Room を開く</button>
        )}
      </div>
    </div>
  )
}

function RejectedJobRow({ job }: { job: Job }) {
  return (
    <div className="glass" style={{ padding: '10px 12px', display: 'grid', gap: 3, border: '1px solid var(--line)', background: 'var(--panel)' }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <span className="mono" style={{ fontSize: 12 }}>{job.job_id}</span>
        <span className="badge b-warn">rejected</span>
        {job.override && <span className="mono muted" style={{ fontSize: 11 }}>{job.override.param}={job.override.to}</span>}
      </div>
      <div className="mono muted" style={{ fontSize: 10.5 }}>親 {job.parent_room}</div>
    </div>
  )
}

export default function Inbox() {
  const catalog = useStore((s) => s.catalog)!
  const toLobby = useStore((s) => s.toLobby)
  const candidates = catalog.candidate_rooms || []
  const jobs = catalog.jobs || []
  const rejected = jobs.filter((j) => j.status === 'rejected')
  const running = jobs.filter((j) => j.status === 'running' || j.status === 'queued')

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '20px 20px 80px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
          <button className="tbtn" onClick={toLobby} aria-label="back">‹</button>
          <div>
            <p className="eyebrow" style={{ margin: '0 0 4px' }}>AI Discovery Inbox</p>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 600, letterSpacing: '-.02em' }}>発見の受信箱</h1>
          </div>
        </div>
        <p className="muted" style={{ fontSize: 12.5, margin: '8px 0 20px', lineHeight: 1.6 }}>
          AI / Live Runner が親 Room の始原条件を変えて実計算した候補。<b>正式 Room とは区別</b>され、
          <b>自己昇格しない</b>。始原条件の差・到達 Level の親比・昇格パイプラインを示す。
        </p>

        {running.length > 0 && (
          <div className="glass" style={{ padding: '10px 12px', marginBottom: 16, border: '1px solid rgba(79,227,224,.3)', background: 'var(--accent-dim)' }}>
            <span className="mono" style={{ fontSize: 11, color: 'var(--accent)' }}>実行中 {running.length} 件</span>
          </div>
        )}

        {candidates.length === 0 ? (
          <div className="muted mono" style={{ fontSize: 13, padding: 24, textAlign: 'center' }}>
            まだ候補はありません。Room の Genesis タブから Live Runner ジョブを発行できます。
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 16 }}>
            {candidates.map((c) => <DiscoveryCard key={c.room_id} room={c} />)}
          </div>
        )}

        {rejected.length > 0 && (
          <>
            <h2 style={{ fontSize: 14, fontWeight: 600, margin: '28px 0 10px', color: 'var(--muted)' }}>棄却されたジョブ</h2>
            <p className="muted" style={{ fontSize: 11.5, margin: '0 0 10px' }}>
              許容範囲外・不許可ノブ・非 g001 親などで実行前に拒否されたもの（Room は作られない）。
            </p>
            <div style={{ display: 'grid', gap: 8 }}>
              {rejected.map((j) => <RejectedJobRow key={j.job_id} job={j} />)}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
