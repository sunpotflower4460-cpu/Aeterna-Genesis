import { useRef } from 'react'
import { useStore } from '../store'
import { useRoomField } from '../lib/useField'
import Viewport from './Viewport'
import type { Room } from '../lib/types'
import { dimBadge } from './ui'

function Panel({ roomId, lensPref, clock, playing, speed, drive, onFrame }: {
  roomId: string; lensPref: string | null; clock: React.MutableRefObject<number>
  playing: boolean; speed: number; drive: boolean; onFrame: (i: number) => void
}) {
  const room = useStore((s) => s.catalog?.rooms.find((r) => r.room_id === roomId)) as Room | undefined
  const data = useRoomField(roomId)
  const lensName = data.lensNames.includes(lensPref || '') ? lensPref! : data.lensNames[0]
  const decoded = lensName ? data.lenses[lensName] : null
  const is3d = data.field?.dimension === 3
  return (
    <div style={{ position: 'relative', overflow: 'hidden', borderRight: '1px solid var(--line)' }}>
      {data.loading && <div className="mono muted" style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', zIndex: 2, fontSize: 12 }}>◈ 読み込み中…</div>}
      {decoded && <Viewport lens={decoded} view={useStore.getState().viewSettings} is3d={is3d}
        playing={playing && drive} speed={speed} clock={clock} nframes={data.field?.nframes ?? 1}
        onFrame={drive ? onFrame : () => {}} />}
      <div className="mono" style={{ position: 'absolute', top: 10, left: 10, fontSize: 10.5 }}>
        <div style={{ background: 'rgba(6,11,20,.6)', border: '1px solid var(--line)', borderRadius: 9, padding: '6px 9px' }}>
          <b>{room?.title?.slice(0, 34)}</b><br />
          <span className="muted">Level {room?.reached_level ?? '?'} · lens {lensName}</span>
        </div>
      </div>
    </div>
  )
}

function diffRows(a?: Room, b?: Room) {
  if (!a || !b) return []
  const rows: [string, string, string][] = [
    ['到達 Level', String(a.reached_level ?? '?'), String(b.reached_level ?? '?')],
    ['次元', a.dimension ?? '', b.dimension ?? ''],
    ['genesis', a.genesis_model ?? '', b.genesis_model ?? ''],
  ]
  return rows
}

export default function CompareView() {
  const catalog = useStore((s) => s.catalog)!
  const [idA, idB] = useStore((s) => s.compareIds)
  const setCompareId = useStore((s) => s.setCompareId)
  const toLobby = useStore((s) => s.toLobby)
  const { lens, playing, speed, frame } = useStore()
  const { setLens, togglePlay, setSpeed, setFrame } = useStore()
  const clock = useRef(0)

  const rooms = catalog.rooms
  const roomA = rooms.find((r) => r.room_id === idA)
  const roomB = rooms.find((r) => r.room_id === idB)
  const lensUnion = Array.from(new Set(rooms.flatMap((r) => r.lenses || [])))

  const Selector = ({ slot, value }: { slot: 0 | 1; value: string }) => (
    <select className="mono" value={value} onChange={(e) => setCompareId(slot, e.target.value)}
      style={{ background: 'var(--panel-solid)', color: 'var(--ink)', border: '1px solid var(--line-2)', borderRadius: 8, padding: '5px 8px', fontSize: 12 }}>
      {rooms.map((r) => <option key={r.room_id} value={r.room_id}>{r.title}</option>)}
    </select>
  )

  return (
    <div style={{ height: '100%', display: 'grid', gridTemplateRows: 'auto 1fr auto auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderBottom: '1px solid var(--line)', flexWrap: 'wrap' }}>
        <button className="tbtn" onClick={toLobby} aria-label="back">‹</button>
        <span style={{ fontWeight: 600 }}>Compare</span>
        <span className="muted mono" style={{ fontSize: 12 }}>同じ時刻・同じレンズで並べる</span>
        <span style={{ flex: 1 }} />
        <Selector slot={0} value={idA} /><span className="muted">vs</span><Selector slot={1} value={idB} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 0 }}>
        {idA && <Panel roomId={idA} lensPref={lens} clock={clock} playing={playing} speed={speed} drive onFrame={(i) => setFrame(i)} />}
        {idB && <Panel roomId={idB} lensPref={lens} clock={clock} playing={playing} speed={speed} drive={false} onFrame={() => {}} />}
      </div>

      {/* diff strip */}
      <div style={{ display: 'flex', gap: 16, padding: '8px 14px', borderTop: '1px solid var(--line)', flexWrap: 'wrap', alignItems: 'center' }}>
        <span className="mono muted" style={{ fontSize: 11 }}>差分:</span>
        {diffRows(roomA, roomB).map(([k, va, vb]) => (
          <span key={k} className="mono" style={{ fontSize: 11 }}>
            <span className="muted">{k}</span> <b style={{ color: va === vb ? 'var(--muted)' : 'var(--accent)' }}>{va} / {vb}</b>
          </span>
        ))}
        {roomA && dimBadge(roomA)}{roomB && dimBadge(roomB)}
      </div>

      {/* shared controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderTop: '1px solid var(--line)', background: 'rgba(6,11,20,.5)' }}>
        <button className="tbtn" onClick={() => { clock.current = 0; setFrame(0) }} aria-label="reset">⏮</button>
        <button className="tbtn pri" onClick={togglePlay} aria-label="play/pause">{playing ? '❚❚' : '▶'}</button>
        <div style={{ display: 'flex', gap: 6, flex: 1, flexWrap: 'wrap' }}>
          {lensUnion.map((l) => (
            <button key={l} className={'lens ' + (l === lens ? 'on' : '')} onClick={() => setLens(l)}>{l}</button>
          ))}
        </div>
        <span className="mono muted tnum" style={{ fontSize: 12 }}>frame {frame}</span>
        <button className="tbtn" onClick={() => setSpeed(speed >= 2 ? 0.5 : speed * 2)} aria-label="speed">×{speed}</button>
      </div>
    </div>
  )
}
