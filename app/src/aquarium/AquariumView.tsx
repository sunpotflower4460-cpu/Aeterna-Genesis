import { useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import { loadTank, loadTemplates } from './data'
import { recordedSource } from './types'
import type { AquariumTemplate, TankField } from './types'
import VolumeTank from './VolumeTank'
import SurfaceTank from './SurfaceTank'
import FieldGuides from './render/FieldGuides'
import FieldLegend from './render/FieldLegend'
import AppearanceControls from './render/AppearanceControls'
import { DEFAULT_APPEARANCE, type Appearance } from './render/appearance'
import { exportFieldPng } from './render/exportPng'

const REDUCED = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

function hasWebGL2(): boolean {
  try { return !!document.createElement('canvas').getContext('webgl2') } catch { return false }
}

/** Advances the shared playback clock (frames per second of *recorded* frames, not physics time). */
function Clock({ clock, playing, fps, nframes, onFrame }: {
  clock: React.MutableRefObject<number>; playing: boolean; fps: number; nframes: number; onFrame: (i: number) => void
}) {
  const last = useRef(-1)
  useFrame((_, dt) => {
    if (playing && nframes > 1) {
      clock.current += Math.min(dt, 0.1) * fps
      if (clock.current > nframes - 1) clock.current = 0
    }
    const i = Math.floor(clock.current)
    if (i !== last.current) { last.current = i; onFrame(i) }
  })
  return null
}

export default function AquariumView({ onOpenObservatory, onOpenLab }: { onOpenObservatory?: () => void; onOpenLab?: () => void }) {
  const [templates, setTemplates] = useState<AquariumTemplate[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [loadedTank, setTank] = useState<TankField | null>(null)
  const [loadedId, setLoadedId] = useState<string | null>(null)
  const [lensName, setLensName] = useState<string | null>(null)
  const [playing, setPlaying] = useState(!REDUCED)
  const [fps, setFps] = useState(6)
  const [frame, setFrame] = useState(0)
  const [appearance, setAppearance] = useState<Appearance>({ ...DEFAULT_APPEARANCE })
  const [showAppearance, setShowAppearance] = useState(false)
  const cameraControls = useRef<any>(null)
  const root = useRef<HTMLDivElement>(null)
  const [threshold, setThreshold] = useState(0.35)
  const [density, setDensity] = useState(0.6)
  const [relief, setRelief] = useState(0.35)
  const [showCard, setShowCard] = useState(() => typeof innerWidth === 'undefined' || innerWidth > 720)
  const clock = useRef(0)
  const webgl2 = useMemo(hasWebGL2, [])

  useEffect(() => {
    loadTemplates().then((t) => {
      setTemplates(t)
      const fromHash = decodeURIComponent(location.hash.replace(/^#/, ''))
      setActiveId(t.some((x) => x.id === fromHash) ? fromHash : t[0]?.id ?? null)
    }).catch((e) => setError(String(e)))
  }, [])

  useEffect(() => {
    if (!templates) return
    const onHash = () => {
      const id = decodeURIComponent(location.hash.replace(/^#/, ''))
      if (templates.some((x) => x.id === id)) setActiveId(id)
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [templates])

  const active = templates?.find((t) => t.id === activeId) ?? null

  // Never label a previous template's recorded field as the newly selected one.
  const tank = loadedId === active?.id ? loadedTank : null

  useEffect(() => {
    if (!active) return
    let alive = true
    setTank(null)
    setLoadedId(null)
    setFrame(0)
    clock.current = 0
    setLensName(active.default_lens)
    if (location.hash !== '#' + active.id) history.replaceState(null, '', '#' + active.id)
    loadTank(active.id).then((f) => { if (alive) { setTank(f); setLoadedId(active.id) } }).catch((e) => alive && setError(String(e)))
    return () => { alive = false }
  }, [active])

  const lensMeta = active?.lenses.find((l) => l.name === lensName) ?? active?.lenses[0]
  const lens = tank && lensMeta ? tank.lenses[lensMeta.name] : null
  const src = useMemo(() => (lens ? recordedSource(lens) : null), [lens])
  const t = tank && tank.times.length ? tank.times[Math.min(frame, tank.times.length - 1)] : 0

  if (error) {
    return <div className="aq-center mono muted">aquarium data unavailable — {error}</div>
  }
  if (!templates || !active) {
    return <div className="aq-center mono muted" style={{ letterSpacing: '.15em' }}>◈ filling the tank…</div>
  }

  return (
    <div className="aq-root" ref={root}>
      <div className="aq-canvas">
        {!webgl2 ? (
          <div className="aq-center mono muted">WebGL2 が必要です（このブラウザでは 3D の水槽を表示できません）</div>
        ) : (
          <Canvas camera={{ position: [1.55, 1.05, 1.55], fov: 42, near: 0.01, far: 20 }} dpr={appearance.quality === 'draft' ? 1 : [1, appearance.quality === 'fine' ? 2 : 1.5]} gl={{ preserveDrawingBuffer: true, antialias: true }}>
            <color attach="background" args={['#05080f']} />
            {appearance.guides && <FieldGuides dimension={tank?.dimension ?? 3}/>}
            {src && tank && lensMeta && (tank.dimension === 3
              ? <VolumeTank src={src} transfer={lensMeta.transfer} clock={clock} threshold={threshold} density={density} appearance={appearance} />
              : <SurfaceTank src={src} transfer={lensMeta.transfer} clock={clock} relief={relief} appearance={appearance} />)}
            {tank && <Clock clock={clock} playing={playing} fps={fps} nframes={tank.nframes} onFrame={setFrame} />}
            <OrbitControls ref={cameraControls} enablePan={false} enableDamping dampingFactor={0.12} minDistance={1.1} maxDistance={5} />
          </Canvas>
        )}
        {!tank && <div className="aq-center mono muted aq-overlay">◈ loading {active.id}…</div>}
      </div>

      <header className="aq-top glass">
        <div className="eyebrow">Aeterna · 水槽</div>
        <h1 className="aq-title">{active.title}</h1>
        <div className="aq-badges">
          <span className="badge b-2d">{active.dimension}D</span>
          <span className="badge b-official">{active.level}</span>
          <span className="badge">{active.tier}</span>
          <span className="badge mono">{active.white}</span>
        </div>
      </header>

      <nav className="aq-carousel" aria-label="テンプレート">
        {templates.map((tp) => (
          <button key={tp.id} className={'aq-chip' + (tp.id === active.id ? ' on' : '')} onClick={() => setActiveId(tp.id)}>
            <span className="mono aq-chip-d">{tp.dimension}D</span> {tp.title}
          </button>
        ))}
        {onOpenLab && <button className="aq-chip aq-lab" onClick={onOpenLab}>● ライブで動かす →</button>}
        {onOpenObservatory && <button className="aq-chip aq-obs" onClick={onOpenObservatory}>Observatory →</button>}
      </nav>

      {showCard ? (
        <aside className="aq-card glass">
          <button className="aq-x tbtn" aria-label="閉じる" onClick={() => setShowCard(false)}>×</button>
          <p className="aq-caption">{active.caption}</p>
          <div className="aq-cols">
            <div>
              <div className="eyebrow aq-put">置いたもの</div>
              <ul>{active.put_in.map((x) => <li key={x}>{x}</li>)}</ul>
            </div>
            <div>
              <div className="eyebrow">育ったもの</div>
              <ul>{active.emerged.map((x) => <li key={x}>{x}</li>)}</ul>
            </div>
          </div>
          <div className="mono muted aq-src">出典: {active.source} · recipe {JSON.stringify(active.recipe)}</div>
          <div className="mono muted aq-src">可視化は表示のみ（物理データは変更しない・uint8 量子化・補間表示）</div>
        </aside>
      ) : (
        <button className="aq-reopen tbtn" onClick={() => setShowCard(true)}>置いた／育った</button>
      )}

      {lens && lensMeta && <div className="aq-visual-tools">
        <FieldLegend label={lensMeta.label} transfer={lensMeta.transfer} palette={appearance.palette} lo={lens.vmin} hi={lens.vmax}/>
        <button className="tbtn" onClick={()=>cameraControls.current?.reset()}>視点を戻す</button>
        <button className="tbtn" aria-expanded={showAppearance} onClick={()=>setShowAppearance(v=>!v)}>描画設定</button>
      </div>}
      {showAppearance && <div className="aq-render-settings">
        <button className="field-settings-close" aria-label="描画設定を閉じる" onClick={()=>setShowAppearance(false)}>×</button>
        <AppearanceControls value={appearance} onChange={setAppearance} dimension={tank?.dimension ?? 3}/>
      </div>}
      <footer className="aq-controls glass">
        <button className="tbtn pri" onClick={() => setPlaying((p) => !p)} aria-label={playing ? '一時停止' : '再生'}>
          {playing ? '❚❚' : '▶'}
        </button>
        <input className="aq-range" type="range" min={0} max={Math.max(0, (tank?.nframes ?? 1) - 1)} step={0.01}
          value={Math.min(frame, (tank?.nframes ?? 1) - 1)} aria-label="時刻"
          onChange={(e) => { clock.current = Number(e.target.value); setFrame(Math.floor(clock.current)) }} />
        <span className="mono tnum aq-time">t={t.toFixed(1)}</span>
        {active.lenses.length > 1 && (
          <select className="aq-select" value={lensMeta?.name} onChange={(e) => setLensName(e.target.value)} aria-label="レンズ">
            {active.lenses.map((l) => <option key={l.name} value={l.name}>{l.label}</option>)}
          </select>
        )}
        {tank?.dimension === 3 ? (
          <>
            <label className="aq-knob mono">しきい<input type="range" min={0.02} max={0.95} step={0.01} value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))} /></label>
            <label className="aq-knob mono">濃さ<input type="range" min={0.1} max={2} step={0.05} value={density}
              onChange={(e) => setDensity(Number(e.target.value))} /></label>
          </>
        ) : (
          <label className="aq-knob mono">起伏<input type="range" min={0} max={0.8} step={0.01} value={relief}
            onChange={(e) => setRelief(Number(e.target.value))} /></label>
        )}
        <button className="tbtn" disabled={!lens || !lensMeta} onClick={()=>{
          const canvas=root.current?.querySelector('canvas')
          if(canvas && lens && lensMeta) exportFieldPng(canvas,[{label:`${active.id} | t=${t.toFixed(2)} | ${lens.name} | ${tank?.dimension}D ${tank?.grid.join('x')}`,lo:lens.vmin,hi:lens.vmax,transfer:lensMeta.transfer}],appearance,{threshold,density,relief}).catch(e=>setError(String(e)))
        }}>PNG保存 ↗</button>
        <label className="aq-knob mono">速さ<input type="range" min={1} max={20} step={1} value={fps}
          onChange={(e) => setFps(Number(e.target.value))} /></label>
      </footer>
    </div>
  )
}
