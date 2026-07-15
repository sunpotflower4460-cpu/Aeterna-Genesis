import { useEffect, useRef, useState } from 'react'
import { useStore } from '../store'
import { useRoomField } from '../lib/useField'
import Viewport from './Viewport'
import Inspector from './Inspector'
import { LEVEL_TEXT, LENS_JP, LENS_LEGEND, dimBadge } from './ui'
import type { Room } from '../lib/types'

export default function RoomWorkspace() {
  const room = useStore((s) => s.currentRoom())
  const { lens, frame, playing, speed, inspectorOpen, viewSettings } = useStore()
  const { setLens, setFrame, togglePlay, setSpeed, toLobby, toggleInspector } = useStore()
  const data = useRoomField(room?.room_id ?? null)
  const nframes = data.field?.nframes ?? 1
  const is3d = data.field?.dimension === 3
  const clock = useRef(0) // smooth playhead in frame units, advanced by the render loop
  const [capOpen, setCapOpen] = useState(true) // "これは何？" caption starts open

  // default lens once fields load
  useEffect(() => {
    if (data.lensNames.length && (!lens || !data.lensNames.includes(lens))) setLens(data.lensNames[0])
  }, [data.lensNames, lens, setLens])

  if (!room) return null
  const decoded = lens ? data.lenses[lens] : null
  // a cyclic (phase) lens is gated by an amplitude sibling (density) so it isn't full-volume rainbow
  const maskLens = decoded?.cyclic
    ? (Object.values(data.lenses).find((l) => l && !l.cyclic) ?? null)
    : null
  const t = data.field?.times[Math.min(frame, nframes - 1)]

  return (
    <div style={{ height: '100%', display: 'grid', gridTemplateRows: 'auto 1fr auto', background: 'var(--ground)' }}>
      {/* header */}
      <div className="room-head" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', borderBottom: '1px solid var(--line)' }}>
        <button className="tbtn" onClick={toLobby} aria-label="back">‹</button>
        <span className="room-title" style={{ fontWeight: 600 }}>{room.title}</span>
        <span className="badge">Level {room.reached_level ?? '?'}</span>
        {dimBadge(room)}
        <span style={{ flex: 1 }} />
        <button className={'tbtn ' + (inspectorOpen ? 'active' : '')} onClick={toggleInspector} aria-label="inspector">☰</button>
      </div>

      {/* viewport + overlays + inspector */}
      <div className="room-body" style={{ position: 'relative', overflow: 'hidden', display: 'grid', gridTemplateColumns: inspectorOpen ? '1fr 300px' : '1fr' }}>
        <div style={{ position: 'relative' }}>
          {data.loading && <Overlay text="◈ recorded field を読み込み中…" />}
          {data.error && <Overlay text={'記録された場がありません（' + data.error + '）'} />}
          {decoded && <Viewport lens={decoded} mask={maskLens} view={viewSettings} is3d={is3d} playing={playing}
            speed={speed} clock={clock} nframes={nframes} onFrame={(i) => setFrame(i)} />}

          {/* "これは何？" plain-language caption — what emerged, level meaning, honesty, what was put in */}
          <Caption room={room} open={capOpen} onToggle={() => setCapOpen((v) => !v)} />

          {/* HUD (compact, top-right) */}
          <Hud pos={{ top: 12, right: 12 }}>
            <b style={{ color: room.official ? 'var(--official)' : 'var(--muted)' }}>{room.dimension}</b><br />
            <span className="muted">{room.runs?.length ?? 0} seeds</span>
          </Hud>
          {t !== undefined && <Hud pos={{ left: 12, bottom: 84 }}>t = <b className="tnum">{t.toFixed(2)}</b></Hud>}

          {/* lens row (JP labels) + color legend for the active lens */}
          <div style={{ position: 'absolute', left: 12, right: 12, bottom: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
            {lens && LENS_LEGEND[lens] && (
              <div className="legend mono muted">🎨 {LENS_LEGEND[lens]}</div>
            )}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {data.lensNames.map((l) => (
                <button key={l} className={'lens ' + (l === lens ? 'on' : '')} onClick={() => setLens(l)}>
                  {LENS_JP[l] ?? l}<span className="lens-en"> {l}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
        {inspectorOpen && <Inspector room={room} data={data} />}
      </div>

      {/* playback bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderTop: '1px solid var(--line)', background: 'rgba(6,11,20,.5)' }}>
        <button className="tbtn" onClick={() => { clock.current = 0; setFrame(0) }} aria-label="reset">⏮</button>
        <button className="tbtn pri" onClick={togglePlay} aria-label="play/pause">{playing ? '❚❚' : '▶'}</button>
        <button className="tbtn" onClick={() => { const n = (frame + 1) % nframes; clock.current = n; setFrame(n) }} aria-label="step">⏭</button>
        <input className="range" type="range" min={0} max={Math.max(0, nframes - 1)} value={Math.min(frame, nframes - 1)}
          onChange={(e) => { const v = Number(e.target.value); clock.current = v; setFrame(v) }} style={{ flex: 1 }} aria-label="timeline" />
        <span className="mono muted tnum" style={{ fontSize: 12, minWidth: 64, textAlign: 'right' }}>
          {t !== undefined ? 't=' + t.toFixed(1) : ''}
        </span>
        <button className="tbtn" onClick={() => setSpeed(speed >= 2 ? 0.5 : speed * 2)} aria-label="speed">×{speed}</button>
        <button className="lens" style={{ color: 'var(--accent)', borderColor: 'rgba(79,227,224,.4)', background: 'var(--accent-dim)' }}
          onClick={() => useStore.getState().setTab('genesis')}>⑃ Branch Room</button>
      </div>
    </div>
  )
}

function Caption({ room, open, onToggle }: { room: Room; open: boolean; onToggle: () => void }) {
  const level = room.reached_level ?? 0
  if (!open) {
    return (
      <button className="cap-chip" onClick={onToggle} aria-label="これは何？">? これは何</button>
    )
  }
  return (
    <div className="caption">
      <div className="cap-head">
        <b>{room.emerged || room.title}</b>
        <button className="cap-x" onClick={onToggle} aria-label="close">×</button>
      </div>
      <div className="cap-line">
        <span className="cap-badge">Level {level}</span>
        <span className="muted">{LEVEL_TEXT[level] ?? ''}</span>
      </div>
      <div className="cap-honest">完成した構造は初期状態に入れていません（0から育った）</div>
      {room.put_in && <div className="cap-putin muted">入れたもの: {room.put_in}</div>}
    </div>
  )
}

function Hud({ pos, children }: { pos: React.CSSProperties; children: React.ReactNode }) {
  return (
    <div className="mono" style={{ position: 'absolute', fontSize: 10.5, ...pos }}>
      <div style={{ background: 'rgba(6,11,20,.55)', backdropFilter: 'blur(6px)', border: '1px solid var(--line)', borderRadius: 9, padding: '6px 9px', lineHeight: 1.4 }}>
        {children}
      </div>
    </div>
  )
}

function Overlay({ text }: { text: string }) {
  return <div className="mono muted" style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', zIndex: 2, fontSize: 12 }}>{text}</div>
}
