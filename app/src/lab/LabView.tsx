import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, View } from '@react-three/drei'
import * as THREE from 'three'
import VolumeTank from '../aquarium/VolumeTank'
import SurfaceTank from '../aquarium/SurfaceTank'
import { api, lab, setActiveGoalId, getActiveGoalId, type KnobSpec, type LabEvent, type UniverseInfo, type WhiteSpec } from './api'
import { useLabStream, type LiveSource, type LiveState } from './live'
import ComparePanel, { seriesColor } from './ComparePanel'
import GuidePanel from './GuidePanel'
import GoalPanel, { type ModelEntry } from './GoalPanel'

// Live lab: several universes side by side, each running its white from t=0 in a worker process on the
// lab server. Everything a person changes is sent as an explicit, recorded intervention (law change or
// perturbation); a branch forks the current state so the only difference is that one intervention.

type Shared = { pos: THREE.Vector3; target: THREE.Vector3; version: number; owner: string }

function Glass() {
  const geo = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(1.002, 1.002, 1.002)), [])
  return (
    <lineSegments geometry={geo}>
      <lineBasicMaterial color="#7aa2cc" transparent opacity={0.35} />
    </lineSegments>
  )
}

/** One OrbitControls per view; whichever view the person drags becomes the owner and the others follow. */
function LinkedControls({ id, shared }: { id: string; shared: React.MutableRefObject<Shared> }) {
  const controls = useRef<any>(null)
  const { camera } = useThree()
  const seen = useRef(-1)
  const dragging = useRef(false)
  useFrame(() => {
    const s = shared.current
    const c = controls.current
    if (!c || dragging.current || seen.current === s.version) return
    camera.position.copy(s.pos)
    c.target.copy(s.target)
    c.update()
    seen.current = s.version
  })
  return (
    <OrbitControls ref={controls} enablePan={false} minDistance={0.8} maxDistance={4}
      onStart={() => { dragging.current = true; shared.current.owner = id }}
      onEnd={() => { dragging.current = false }}
      onChange={() => {
        if (!dragging.current || !controls.current) return
        const s = shared.current
        s.pos.copy(camera.position)
        s.target.copy(controls.current.target)
        s.version++
        seen.current = s.version
      }} />
  )
}

/** Clear the whole canvas before the views draw: when the grid re-flows (a universe is added or closed),
 *  areas no longer covered by any view would otherwise keep stale pixels. Negative priority runs first and
 *  does not take over rendering. */
function ClearAll() {
  useFrame(({ gl }) => {
    gl.setScissorTest(false)
    gl.setClearColor('#05080f', 0)
    gl.clear(true, true, true)
  }, -1)
  return null
}

/** Tall, narrow views (phones) widen the field of view so the whole tank stays in frame. */
function Camera() {
  const { size } = useThree()
  const aspect = size.width / Math.max(size.height, 1)
  const fov = aspect < 1 ? Math.min(80, 42 / Math.pow(aspect, 0.75)) : 42
  return <PerspectiveCamera makeDefault position={[1.25, 0.85, 1.35]} fov={fov} near={0.01} far={20} />
}

function LiveClock({ src, clock }: { src: LiveSource; clock: React.MutableRefObject<number> }) {
  useFrame(() => { clock.current = src.position(performance.now()) })
  return null
}

function TankScene({ id, dimension, src, transfer, shared, threshold, density, relief }: {
  id: string; dimension: 2 | 3; src: LiveSource; transfer: WhiteSpec['lenses'][number]['transfer']
  shared: React.MutableRefObject<Shared>; threshold: number; density: number; relief: number
}) {
  const clock = useRef(0)
  return (
    <>
      <color attach="background" args={['#05080f']} />
      <Camera />
      <LinkedControls id={id} shared={shared} />
      <Glass />
      <LiveClock src={src} clock={clock} />
      {dimension === 3
        ? <VolumeTank src={src} transfer={transfer} clock={clock} threshold={threshold} density={density} />
        : <SurfaceTank src={src} transfer={transfer} clock={clock} relief={relief} />}
    </>
  )
}

/** Current knob values of a universe = initial knobs, then every recorded law change in order. */
function currentKnobs(u: UniverseInfo): Record<string, number> {
  const k = { ...u.recipe.knobs }
  for (const ev of u.recipe.events) if (ev.kind === 'set' && ev.values) Object.assign(k, ev.values)
  return k
}

/** Short name of a white for headers: the part in the last （…） of its title, if any. */
export function shortTitle(w: WhiteSpec | undefined, fallback = ''): string {
  if (!w) return fallback
  const m = w.title.match(/（([^（）]+)）\s*$/)
  return m ? m[1] : w.title
}

function describeEvent(ev: LabEvent, w: WhiteSpec | undefined): string {
  const t = (ev.step * (w?.dt ?? 1)).toFixed(1)
  if (ev.kind === 'set') {
    return `t=${t}  ` + Object.entries(ev.values ?? {}).map(([k, v]) => `${w?.knobs.find((x) => x.name === k)?.label ?? k}=${v}`).join(', ')
  }
  const p = w?.perturbs.find((x) => x.name === ev.name)
  const args = Object.entries(ev.args ?? {}).map(([k, v]) => `${k}=${v}`).join(', ')
  return `t=${t}  ${p?.label ?? ev.name}${args ? ` (${args})` : ''}`
}

function Slider({ k, value, onChange, changed }: { k: KnobSpec; value: number; onChange: (v: number) => void; changed?: boolean }) {
  return (
    <label className={'lab-knob' + (changed ? ' changed' : '')} title={`${k.name}（${k.lo}〜${k.hi}）`}>
      <span>{k.label}</span>
      <input type="range" min={k.lo} max={k.hi} step={k.step} value={value} onChange={(e) => onChange(Number(e.target.value))} />
      <span className="mono tnum">{k.integer ? value.toFixed(0) : Number(value.toPrecision(4))}</span>
    </label>
  )
}

function NewUniverse({ whites, onCreate, disabled }: { whites: WhiteSpec[]; onCreate: (w: string, seed: number, knobs: Record<string, number>) => void; disabled: boolean }) {
  const [wid, setWid] = useState(whites.find((w) => w.dimension === 3)?.id ?? whites[0]?.id ?? '')
  const w = whites.find((x) => x.id === wid)
  const [seed, setSeed] = useState(0)
  const [knobs, setKnobs] = useState<Record<string, number>>({})
  useEffect(() => { setKnobs({}) }, [wid])
  if (!w) return null
  const val = (k: KnobSpec) => knobs[k.name] ?? k.default
  return (
    <details className="lab-section lab-new" open={!disabled}>
      <summary>＋ 新しい実験をはじめる</summary>
      <select className="aq-select" aria-label="実験の場" value={wid} onChange={(e) => setWid(e.target.value)}>
        {whites.map((x) => <option key={x.id} value={x.id}>{x.title}</option>)}
      </select>
      <div className="muted lab-note">t=0 に置くもの: {w.put_in.join(' / ')}</div>
      <button className="tbtn pri" disabled={disabled} onClick={() => onCreate(wid, seed, knobs)}>▶ この場を時刻0から動かす</button>
      <details className="lab-fold">
        <summary>つまみと seed を変える</summary>
        <label className="lab-knob"><span>seed</span>
          <input type="number" min={0} max={9999} value={seed} onChange={(e) => setSeed(Number(e.target.value) || 0)} /></label>
        {w.knobs.map((k) => <Slider key={k.name} k={k} value={val(k)} changed={knobs[k.name] !== undefined && knobs[k.name] !== k.default}
          onChange={(v) => setKnobs((o) => ({ ...o, [k.name]: v }))} />)}
      </details>
      {disabled && <div className="muted lab-note">同時に動かせる数の上限です。どれかを閉じてください。</div>}
    </details>
  )
}

function Controls({ u, w, lens, setLens, onError, refresh }: {
  u: UniverseInfo; w: WhiteSpec; lens: string; setLens: (l: string) => void; onError: (e: unknown) => void; refresh: () => void
}) {
  const now = currentKnobs(u)
  const [draft, setDraft] = useState<Record<string, number>>({})
  const [pargs, setPargs] = useState<Record<string, Record<string, number>>>({})
  useEffect(() => { setDraft({}); setPargs({}) }, [u.id])
  const changes = Object.fromEntries(Object.entries(draft).filter(([k, v]) => v !== now[k]))
  const hasChanges = Object.keys(changes).length > 0
  const run = (p: Promise<unknown>) => p.then(() => { setDraft({}); refresh() }).catch(onError)
  const law = w.knobs.filter((k) => k.kind === 'law')

  return (
    <>
      <div className="lab-row">
        <button className="tbtn pri" onClick={() => lab.control(u.id, u.playing ? 'pause' : 'play').then(refresh).catch(onError)}>
          {u.playing ? '❚❚ 止める' : '▶ 動かす'}</button>
        <button className="tbtn" onClick={() => lab.control(u.id, 'step', { n: 1 }).catch(onError)}>1 コマ</button>
        <label className="aq-knob mono">速さ<input type="range" min={0.25} max={6} step={0.25} value={u.speed}
          onChange={(e) => lab.control(u.id, 'speed', { value: Number(e.target.value) }).then(refresh).catch(onError)} /></label>
        {w.lenses.length > 1 && (
          <select className="aq-select" value={lens} onChange={(e) => setLens(e.target.value)} aria-label="レンズ">
            {w.lenses.map((l) => <option key={l.name} value={l.name}>{l.label}</option>)}
          </select>
        )}
      </div>

      <div className="lab-section">
        <div className="eyebrow" title="途中で変えられる。変えたことは「置いたもの」として記録される">つまみ（場の法則）</div>
        {law.map((k) => <Slider key={k.name} k={k} value={draft[k.name] ?? now[k.name] ?? k.default}
          changed={changes[k.name] !== undefined} onChange={(v) => setDraft((o) => ({ ...o, [k.name]: v }))} />)}
        <div className="lab-row">
          <button className="tbtn pri" disabled={!hasChanges} onClick={() => run(lab.create(w.id, u.recipe.seed, { ...u.recipe.knobs, ...changes }, getActiveGoalId()))}
            title="最初のレシピを引き継ぎ、選んだ条件だけ変えて時刻0から計算する">時刻0から別の実験で試す</button>
          <button className="tbtn" disabled={!hasChanges} onClick={() => run(lab.branch(u.id, { set: changes }))}>途中から分岐（介入）</button>
          <button className="tbtn" disabled={!hasChanges} onClick={() => run(lab.set(u.id, changes))}>途中で変更（介入）</button>
          {hasChanges && <button className="tbtn" onClick={() => setDraft({})}>戻す</button>}
        </div>
      </div>

      <details className="lab-section lab-fold">
        <summary>手で加える（摂動）</summary>
        {w.perturbs.map((p) => {
          const a = { ...Object.fromEntries(p.args.map((x) => [x.name, x.default])), ...(pargs[p.name] ?? {}) }
          return (
            <div key={p.name} className="lab-perturb">
              <div>{p.label}</div>
              {p.args.map((x) => <Slider key={x.name} k={x} value={a[x.name]}
                onChange={(v) => setPargs((o) => ({ ...o, [p.name]: { ...(o[p.name] ?? {}), [x.name]: v } }))} />)}
              <div className="lab-row">
                <button className="tbtn" onClick={() => run(lab.branch(u.id, { perturb: { name: p.name, args: a } }))}>分岐して</button>
                <button className="tbtn" onClick={() => run(lab.perturb(u.id, p.name, a))}>この宇宙に</button>
              </div>
            </div>
          )
        })}
      </details>

      <details className="lab-section lab-fold">
        <summary><span className="aq-put">置いたもの</span>（{1 + u.recipe.events.length} 件）</summary>
        <ul className="lab-events">
          <li>t=0  {u.put_in.join(' / ')}（seed {u.recipe.seed}）</li>
          {Object.entries(u.recipe.knobs).filter(([k, v]) => w.knobs.find((x) => x.name === k)?.default !== v)
            .map(([k, v]) => <li key={k}>t=0  {w.knobs.find((x) => x.name === k)?.label ?? k}={v}</li>)}
          {u.recipe.events.map((ev, i) => <li key={i} className={u.fork_index !== null && i >= u.fork_index ? 'fork' : ''}>{describeEvent(ev, w)}</li>)}
        </ul>
      </details>
      <div className="lab-row">
        <button className="tbtn" onClick={() => lab.remove(u.id).then(refresh).catch(onError)}>この宇宙を閉じる</button>
      </div>
    </>
  )
}

function Lineage({ universes, whites, selected, onSelect }: {
  universes: UniverseInfo[]; whites: WhiteSpec[]; selected: string | null; onSelect: (id: string) => void
}) {
  const byParent = new Map<string | null, UniverseInfo[]>()
  for (const u of universes) {
    const p = u.parent && universes.some((x) => x.id === u.parent) ? u.parent : null
    byParent.set(p, [...(byParent.get(p) ?? []), u])
  }
  const node = (u: UniverseInfo, depth: number): JSX.Element => {
    const w = whites.find((x) => x.id === u.white)
    const fork = u.fork_index !== null ? u.recipe.events.slice(u.fork_index) : []
    return (
      <div key={u.id}>
        <button className={'lab-node' + (u.id === selected ? ' on' : '')} style={{ marginLeft: depth * 16 }} onClick={() => onSelect(u.id)}>
          <i style={{ background: seriesColor(u.label) }} /><b>{u.label}</b> {shortTitle(w, u.white)}
          {fork.length > 0 && <span className="mono muted"> ← {fork.map((e) => describeEvent(e, w)).join('; ')}</span>}
        </button>
        {(byParent.get(u.id) ?? []).map((c) => node(c, depth + 1))}
      </div>
    )
  }
  return <div>{(byParent.get(null) ?? []).map((u) => node(u, 0))}</div>
}

/** 「研究記録にする」: write summary + recipes + thumbnails to research/sessions/ (then replay to check). */
function ExportBox({ ids, onError }: { ids: string[]; onError: (e: unknown) => void }) {
  const [note, setNote] = useState('')
  const [done, setDone] = useState<{ dir: string; name: string; bytes: number; universes: string[] } | null>(null)
  return (
    <div className="lab-section">
      <div className="eyebrow">研究記録にする</div>
      <textarea className="lab-note-input" rows={2} value={note} onChange={(e) => setNote(e.target.value)}
        placeholder="メモ（何を確かめたかったか、気づいたこと）" />
      <div className="lab-row">
        <button className="tbtn pri" disabled={!ids.length}
          onClick={() => api<{ dir: string; name: string; bytes: number; universes: string[] }>('journal/export', { method: 'POST', body: { ids, note } })
            .then((r) => { setDone(r); setNote('') }).catch(onError)}>いまの宇宙 {ids.length} 個を書き出す</button>
      </div>
      {done && <p className="lab-note">書き出しました：<code>research/sessions/{done.name}</code></p>}
      <details className="lab-fold">
        <summary>くわしく</summary>
        <p className="muted lab-note">要約（summary.md）・レシピ（recipes.json）・最後のキーフレームだけ（1 MB 以下）。見たことの記録で、主張ではありません。
          t=0 から同じになるかは <code>python -m tools.lab.replay research/sessions/&lt;名前&gt;</code> で確かめられます。
          commit するかどうかは、うえきさんが決めます。</p>
        {done && <p className="mono muted lab-note">{(done.bytes / 1024).toFixed(0)} KB・宇宙 {done.universes.join(', ')}</p>}
      </details>
    </div>
  )
}

export default function LabView({ onExit }: { onExit: () => void }) {
  const [whites, setWhites] = useState<WhiteSpec[]>([])
  const [universes, setUniverses] = useState<UniverseInfo[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [lenses, setLenses] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'ctl' | 'goal' | 'ai' | 'cmp' | 'tree'>('ai')
  const [activeGoal, setActiveGoalState] = useState<string | null>(getActiveGoalId())
  const [models, setModels] = useState<ModelEntry[]>([])
  const setActiveGoal = (id: string | null) => { setActiveGoalId(id); setActiveGoalState(id) }
  const [panel, setPanel] = useState(true)
  const [creating, setCreating] = useState(false)
  const [compact, setCompact] = useState(() => matchMedia('(max-width: 720px)').matches)
  useEffect(() => {
    const media = matchMedia('(max-width: 720px)')
    const update = () => setCompact(media.matches)
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])
  const [range, setRange] = useState<'fixed' | 'frame'>('fixed')
  const [threshold, setThreshold] = useState(0.35)
  const [density, setDensity] = useState(0.6)
  const [relief, setRelief] = useState(0.35)
  const [maxU, setMaxU] = useState(4)
  const root = useRef<HTMLDivElement>(null!)
  const shared = useRef<Shared>({ pos: new THREE.Vector3(1.25, 0.85, 1.35), target: new THREE.Vector3(), version: 0, owner: '' })

  const onError = useCallback((e: unknown) => setError(String(e instanceof Error ? e.message : e)), [])
  const refresh = useCallback(() => { lab.universes().then(setUniverses).catch(onError) }, [onError])

  useEffect(() => {
    lab.whites().then(setWhites).catch(onError)
    api<{ models: ModelEntry[] }>('models').then((d) => setModels(d.models)).catch(() => {})
    api<{ max_universes: number }>('health').then((h) => h.max_universes && setMaxU(h.max_universes)).catch(() => {})
    refresh()
  }, [refresh, onError])

  useEffect(() => {
    setSelected((current) => current && universes.some((u) => u.id === current)
      ? current : universes[universes.length - 1]?.id ?? null)
  }, [universes])

  const lensOf = (u: UniverseInfo) => {
    const w = whites.find((x) => x.id === u.white)
    return w?.lenses.find((l) => l.name === lenses[u.id]) ?? w?.lenses[0]
  }
  const subs = universes.flatMap((u) => {
    const l = lensOf(u)
    const w = whites.find((x) => x.id === u.white)
    // same display grid as tools/lab/universe.Universe.display_grid()
    const grid = w ? w.grid.map((n) => Math.min(n, w.dimension === 3 ? 48 : 128)) : []
    return l && w ? [{ id: u.id, lens: l.name, vmin: l.vmin, vmax: l.vmax, cyclic: l.cyclic, grid }] : []
  })
  const { sources, history, live } = useLabStream(subs, refresh)
  sources.forEach((s) => { s.mode = range })

  const merged: UniverseInfo[] = universes.map((u) => ({ ...u, ...(live[u.id] as Partial<LiveState> | undefined) }))
  const sel = merged.find((u) => u.id === selected) ?? null
  const selWhite = sel ? whites.find((w) => w.id === sel.white) : undefined
  const tick = Object.values(live).reduce((a, s) => a + s.step, 0)
  const cols = merged.length <= 1 ? 1 : 2

  const showExperiment = (id: string) => lab.universes().then((rows) => {
    setUniverses(rows)
    if (rows.some((u) => u.id === id)) setSelected(id)
  }).catch(onError)
  const create = (w: string, seed: number, knobs: Record<string, number>) => {
    if (creating) return
    setCreating(true)
    lab.create(w, seed, knobs, activeGoal).then((u) => showExperiment(u.id))
      .catch(onError).finally(() => setCreating(false))
  }
  const batchControl = (action: 'play' | 'pause') => Promise.all(universes.map((u) => lab.control(u.id, action))).then(refresh).catch(onError)

  return (
    <div className="lab-root" ref={root}>
      <header className="lab-top">
        <div className="lab-brand"><span className="lab-brand-symbol" aria-hidden="true">◈</span><div><strong>Aeterna Genesis</strong><span>INTERACTIVE RESEARCH LAB</span></div></div>
        <div className="lab-live-badge"><i />LIVE LAB</div>
        <div className="lab-top-actions">
          <button className="tbtn" aria-expanded={panel} onClick={() => setPanel((p) => !p)}>{panel ? '画面を広く' : '質問・操作を開く'}</button>
          <button className="tbtn" onClick={onExit}>記録を見る ↗</button>
        </div>
      </header>
      <div className="lab-workspace-heading"><div><span className="eyebrow">OBSERVE / ASK / EXPLORE</span><h1>もしも、を目の前で。</h1></div>
        <p>場を動かす。気になることを聞く。条件を変えて、確かめる。</p></div>
      {error && <div className="lab-error lab-global-error" role="alert"><span>{error}</span><button className="tbtn" aria-label="エラーを閉じる" onClick={() => setError(null)}>×</button></div>}
      <div className={'lab-body' + (panel ? ' with-panel' : '')}>
        <main className="lab-stage">
        <div className="lab-stage-top"><span><i className="lab-connection connected" />{merged.length ? `観測中 · ${merged.length}個の実験` : '実験のワークスペース'}</span>
          <span className="mono">{merged.length}/{maxU} SLOTS</span></div>
        {compact && merged.length > 1 && <nav className="lab-universe-switcher" aria-label="表示する実験">
          {merged.map((u) => <button key={u.id} className={u.id === selected ? 'on' : ''} aria-pressed={u.id === selected} onClick={() => setSelected(u.id)}>
            <i style={{ background: seriesColor(u.label) }} />実験 {u.label}</button>)}
        </nav>}
        <div className={'lab-grid' + (!merged.length ? ' is-empty' : '')} style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
          {merged.length === 0 && <div className="lab-start">
            <div className="lab-start-orbit" aria-hidden="true"><i /><i /><i /><span>◈</span></div>
            <span className="eyebrow">START WITH A FIELD</span><h2>ひとつの場から、<br />あなたの問いをはじめよう。</h2>
            <p>最初の状態と法則を与え、時刻0から計算します。<br />何が起きるかは、動かしながら観測します。</p>
            <div className="lab-starter-cards">
              {whites.filter((w) => ['tdgl-3d', 'gpe-quench-3d'].includes(w.id)).map((w) => <button className="lab-starter-card" key={w.id} disabled={creating} onClick={() => create(w.id, 0, {})}>
                <span className="lab-starter-meta">3D FIELD <span>↗</span></span><strong>{w.id === 'tdgl-3d' ? '冷えていく複素場' : '超流体の場'}</strong><span>{w.family} · {w.grid.join(' × ')}</span><b>{creating ? '準備中…' : 'この場で始める →'}</b>
              </button>)}
            </div>
            <button className="tbtn lab-other-fields" onClick={() => { setTab('ctl'); setPanel(true) }}>すべての場・始原条件を選ぶ →</button>
          </div>}
          {(compact ? merged.filter((u) => u.id === selected) : merged).map((u) => {
            const l = lensOf(u)
            const src = sources.get(u.id)
            const w = whites.find((x) => x.id === u.white)
            const fork = u.fork_index !== null ? u.recipe.events.slice(u.fork_index) : []
            return (
              <div key={u.id} className={'lab-cell' + (u.id === selected ? ' on' : '')} onPointerDown={() => setSelected(u.id)}
                tabIndex={0} role="group" aria-label={`実験 ${u.label} ${shortTitle(w)} ${u.dimension}D`} onFocus={() => setSelected(u.id)}
                style={{ borderColor: u.id === selected ? seriesColor(u.label) : undefined }}>
                {src && l && w && (
                  <View className="lab-view">
                    <TankScene id={u.id} dimension={w.dimension} src={src} transfer={l.transfer} shared={shared}
                      threshold={threshold} density={density} relief={relief} />
                  </View>
                )}
                <div className="lab-cell-head">
                  <b className="lab-universe-letter" style={{ background: seriesColor(u.label) }}>{u.label}</b> <span title={w?.title}>{shortTitle(w, u.white)}</span>
                  <span className="lab-dimension">{u.dimension}D</span><span className="mono muted"> t={u.t.toFixed(1)}{u.playing ? ' · 計算中' : ' · 一時停止'}</span>
                  {u.parent && <span className="mono muted lab-fork" title={fork.map((e) => describeEvent(e, w)).join('; ')}>
                    {' '}← {universes.find((x) => x.id === u.parent)?.label ?? u.parent}</span>}
                  {u.diverged && <div className="lab-diverged" title="物理ではなく計算の限界。つまみを戻して分岐し直してください">数値が発散したので止めました</div>}
                </div>
                <div className="lab-cell-foot">
                  <span className="lab-measured-label">実測値 <small>step {u.step}</small></span>
                  <div className="lab-metric-strip">{Object.entries(u.metrics).slice(0, 3).map(([k, v]) => <div key={k}><span>{k}</span><b className="mono">{typeof v === 'number' && Number.isFinite(v) ? Number(v.toPrecision(4)).toString() : '—'}</b></div>)}</div>
                  <span className="lab-lens-note">{l?.label} · {range === 'fixed' ? '固定の色範囲' : '各コマで色を調整'}{u.dimension === 2 ? ' · 2D場の表示' : ''}</span>
                </div>
              </div>
            )
          })}
        </div>
        {sel && <div className="lab-transport">
          <div className="lab-row"><span className="lab-selected-pill" style={{ borderColor: seriesColor(sel.label) }}>実験 {sel.label}</span>
            <button className="tbtn pri" onClick={() => lab.control(sel.id, sel.playing ? 'pause' : 'play').then(refresh).catch(onError)}>{sel.playing ? '❚❚ 一時停止' : '▶ 再開'}</button>
            <button className="tbtn" onClick={() => lab.control(sel.id, 'step', { n: 1 }).then(refresh).catch(onError)}>1コマ進める</button>
            <button className="tbtn" onClick={() => { setTab('ai'); setPanel(true); requestAnimationFrame(() => document.getElementById('lab-question')?.focus()) }}>✳ この実験について聞く</button>
          </div>
          <div className="lab-row"><button className="tbtn" onClick={() => batchControl(merged.some((u) => u.playing) ? 'pause' : 'play')}>{merged.some((u) => u.playing) ? 'すべて停止' : 'すべて再開'}</button>
            <button className="tbtn" onClick={() => { setTab('cmp'); setPanel(true) }}>測定値を比較 ↗</button></div>
        </div>}
        <div className="lab-stage-caption"><span>実際に計算した場を可視化</span><span>{merged.length > 1 ? '各実験の時刻は独立です · ドラッグで視点を同期' : 'ドラッグで回転 · スクロールで拡大'}</span></div>
      <Canvas className="lab-canvas" eventSource={root} dpr={[1, 2]} gl={{ preserveDrawingBuffer: true }}>
        <ClearAll />
        <View.Port />
      </Canvas>
        </main>
          <aside hidden={!panel} className="lab-panel glass">
            <nav className="lab-tabs" aria-label="研究パネル">
              <button className={tab === 'ctl' ? 'on' : ''} onClick={() => setTab('ctl')}>条件</button>
              <button className={tab === 'goal' ? 'on' : ''} onClick={() => setTab('goal')}>研究</button>
              <button className={tab === 'ai' ? 'on' : ''} onClick={() => setTab('ai')}>✳ AIと試す</button>
              <button className={tab === 'cmp' ? 'on' : ''} onClick={() => setTab('cmp')}>比較</button>
              <button className={tab === 'tree' ? 'on' : ''} onClick={() => setTab('tree')}>記録</button>
            </nav>
            {tab === 'ctl' && (
              <>
                {sel && selWhite && (
                  <div className="lab-section">
                    <div className="lab-sel" title={selWhite.title}><b style={{ color: seriesColor(sel.label) }}>{sel.label}</b> {shortTitle(selWhite)}
                      <span className="mono muted"> t={sel.t.toFixed(0)}</span></div>
                    <Controls u={sel} w={selWhite} lens={lensOf(sel)?.name ?? ''} onError={onError} refresh={refresh}
                      setLens={(l) => setLenses((o) => ({ ...o, [sel.id]: l }))} />
                  </div>
                )}
                {whites.length > 0 && <NewUniverse whites={whites} onCreate={create} disabled={creating || universes.length >= maxU} />}
                <details className="lab-section lab-fold">
                  <summary>見え方（表示だけ）</summary>
                  <div className="lab-row">
                    <label className="aq-knob mono"><input type="radio" checked={range === 'fixed'} onChange={() => setRange('fixed')} />固定の範囲</label>
                    <label className="aq-knob mono"><input type="radio" checked={range === 'frame'} onChange={() => setRange('frame')} />コマごとに伸ばす</label>
                  </div>
                  <div className="lab-row">
                    <label className="aq-knob mono">しきい<input type="range" min={0.02} max={0.95} step={0.01} value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} /></label>
                    <label className="aq-knob mono">濃さ<input type="range" min={0.1} max={2} step={0.05} value={density} onChange={(e) => setDensity(Number(e.target.value))} /></label>
                    <label className="aq-knob mono">起伏<input type="range" min={0} max={0.8} step={0.01} value={relief} onChange={(e) => setRelief(Number(e.target.value))} /></label>
                  </div>
                </details>
              </>
            )}
            {tab === 'cmp' && <ComparePanel universes={merged} history={history} tick={tick} />}
            {tab === 'goal' && <GoalPanel whites={whites} models={models} activeGoal={activeGoal} setActiveGoal={setActiveGoal} onError={onError} onUniverse={refresh} />}
            <div hidden={tab !== 'ai'}>
                <GuidePanel universes={merged} selected={selected} whites={whites} models={models} onError={onError} onBranched={showExperiment} />
            </div>
            {tab === 'tree' && (
              <>
                <Lineage universes={merged} whites={whites} selected={selected} onSelect={setSelected} />
                <ExportBox ids={universes.map((u) => u.id)} onError={onError} />
              </>
            )}
          </aside>
      </div>


    </div>
  )
}
