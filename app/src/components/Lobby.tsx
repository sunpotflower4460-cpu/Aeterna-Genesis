import { useStore } from '../store'
import type { Room } from '../lib/types'
import { dimBadge, physicsBadge, LevelChip } from './ui'

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

export default function Lobby() {
  const catalog = useStore((s) => s.catalog)!
  const rooms = catalog.rooms
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
      </div>
    </div>
  )
}
