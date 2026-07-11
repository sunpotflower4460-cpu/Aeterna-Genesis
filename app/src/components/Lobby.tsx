import { useStore } from '../store'
import type { Room, CandidateRoom, Job } from '../lib/types'
import { dimBadge, physicsBadge, candidateBadge, LevelChip } from './ui'

function Preview({ room }: { room: Room }) {
  // lightweight, honest placeholder tint by dimension (real 3D preview binds on open)
  const tint = room.dimension === 'full-3d' ? '79,227,224' : '107,168,255'
  return (
    <div style={{
      height: 128, borderRadius: 12, position: 'relative', overflow: 'hidden',
      background: `radial-gradient(120% 90% at 60% 35%, rgba(${tint},.28), transparent 60%),
                   radial-gradient(80% 70% at 30% 70%, rgba(169,139,250,.16), transparent 60%), #04070e`,
    }}>
      <div className="mono" style={{ position: 'absolute', left: 10, bottom: 8, fontSize: 10, color: 'var(--faint)' }}>
        {(room.lenses || []).join(' · ') || 'recorded field'}
      </div>
    </div>
  )
}

function Card({ room }: { room: Room }) {
  const openRoom = useStore((s) => s.openRoom)
  return (
    <button className="glass" onClick={() => openRoom(room.room_id)} style={{
      textAlign: 'left', padding: 14, display: 'grid', gap: 12, border: '1px solid var(--line)',
      background: 'var(--panel)', color: 'var(--ink)',
    }}>
      <Preview room={room} />
      <div style={{ display: 'grid', gap: 8 }}>
        <div style={{ fontWeight: 600, fontSize: 15 }}>{room.title}</div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <LevelChip room={room} />{dimBadge(room)}{physicsBadge(room)}
        </div>
        <div className="muted" style={{ fontSize: 12.5, lineHeight: 1.5 }}>{room.emerged}</div>
        <div className="mono" style={{ fontSize: 11, color: 'var(--accent)' }}>開く →</div>
      </div>
    </button>
  )
}

function CandidateCard({ room }: { room: CandidateRoom }) {
  const openRoom = useStore((s) => s.openRoom)
  const hasFields = !!room.frames_ref
  return (
    <button className="glass" onClick={() => openRoom(room.room_id)} disabled={!hasFields} style={{
      textAlign: 'left', padding: 14, display: 'grid', gap: 10, border: '1px dashed var(--line)',
      background: 'var(--panel)', color: 'var(--ink)', opacity: hasFields ? 1 : 0.6,
    }}>
      <div style={{ fontWeight: 600, fontSize: 14 }}>{room.title}</div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {candidateBadge()}
        <span className="badge">Level {room.reached_level ?? '?'}</span>
        <span className="badge">親 {room.parent_room}</span>
      </div>
      <div className="mono" style={{ fontSize: 10.5, color: 'var(--faint)' }}>
        {(room.lenses || []).join(' · ') || '記録なし（screen のみ）'} · full_3d={room.dimension_status?.full_3d ?? '—'}
      </div>
      <div className="mono" style={{ fontSize: 11, color: hasFields ? 'var(--accent)' : 'var(--faint)' }}>
        {hasFields ? '再生 →' : '再生できる場が未記録'}
      </div>
    </button>
  )
}

function JobRow({ job }: { job: Job }) {
  const openRoom = useStore((s) => s.openRoom)
  const color = job.status === 'done' ? 'var(--official)' : job.status === 'rejected' ? 'var(--warn)' : 'var(--muted)'
  return (
    <div className="glass" style={{ padding: '10px 12px', display: 'grid', gap: 4, border: '1px solid var(--line)', background: 'var(--panel)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span className="mono" style={{ fontSize: 12 }}>{job.job_id}</span>
        <span className="badge" style={{ color }}>{job.status}</span>
        {job.override && <span className="mono muted" style={{ fontSize: 11 }}>{job.override.param}={job.override.to}</span>}
        <span style={{ flex: 1 }} />
        {job.result_room && (
          <button className="lens" style={{ color: 'var(--accent)', borderColor: 'rgba(79,227,224,.4)' }}
            onClick={() => openRoom(job.result_room!)}>候補 Room を開く →</button>
        )}
      </div>
      <div className="mono muted" style={{ fontSize: 10.5 }}>
        親 {job.parent_room} · seed {job.seed}
        {job.reached_level != null && <> · reached L{job.reached_level}</>}
        {job.checksum && <> · sha {job.checksum}</>}
      </div>
    </div>
  )
}

export default function Lobby() {
  const catalog = useStore((s) => s.catalog)!
  const rooms = catalog.rooms
  const candidates = catalog.candidate_rooms || []
  const jobs = catalog.jobs || []
  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <div style={{ maxWidth: 1080, margin: '0 auto', padding: '28px 20px 80px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <p className="eyebrow" style={{ margin: '0 0 8px' }}>Aeterna Genesis · Observatory</p>
            <h1 style={{ margin: 0, fontSize: 30, fontWeight: 600, letterSpacing: '-.02em' }}>あなたの宇宙</h1>
            <p className="muted" style={{ margin: '6px 0 0' }}>始原条件から育った宇宙を選ぶ</p>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {rooms.length >= 2 && (
              <button className="lens" onClick={() => useStore.getState().toCompare(rooms[0].room_id, rooms[1].room_id)}>
                ◫ Compare
              </button>
            )}
            <span className="mono muted" style={{ fontSize: 12 }}>
              {rooms.length} rooms · {catalog.evidence_library?.count ?? 0} evidence
            </span>
          </div>
        </div>

        <h2 style={{ fontSize: 15, fontWeight: 600, margin: '28px 0 12px', color: 'var(--muted)' }}>正式 Genesis Rooms</h2>
        <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))' }}>
          {rooms.map((r) => <Card key={r.room_id} room={r} />)}
        </div>

        {candidates.length > 0 && (
          <>
            <h2 style={{ fontSize: 15, fontWeight: 600, margin: '32px 0 6px', color: 'var(--muted)' }}>候補 Rooms（非公式）</h2>
            <p className="muted" style={{ fontSize: 12, margin: '0 0 12px' }}>
              Live Runner / AI が実計算した候補。正式 Room とは区別され、自己昇格しない（full-3D 昇格・格子収束は別段階）。
            </p>
            <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))' }}>
              {candidates.map((c) => <CandidateCard key={c.room_id} room={c} />)}
            </div>
          </>
        )}

        {jobs.length > 0 && (
          <>
            <h2 style={{ fontSize: 15, fontWeight: 600, margin: '32px 0 6px', color: 'var(--muted)' }}>Live Runner ジョブ台帳</h2>
            <p className="muted" style={{ fontSize: 12, margin: '0 0 12px' }}>
              UI が依頼 → Python worker（<span className="mono">tools/run_job.py</span>）が本物のモデルを t=0 から実行した記録。ブラウザは物理を計算しない。
            </p>
            <div style={{ display: 'grid', gap: 8 }}>
              {jobs.map((j) => <JobRow key={j.job_id} job={j} />)}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
