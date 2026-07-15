import { useState } from 'react'
import { useStore } from '../store'
import type { InspectorTab } from '../store'
import type { Room } from '../lib/types'
import type { RoomData } from '../lib/useField'
import { LEVEL_TEXT } from './ui'

const GL_MODEL = 'g001_ginzburg_landau_quench'

const TABS: InspectorTab[] = ['view', 'genesis', 'physics']

export default function Inspector({ room, data }: { room: Room; data: RoomData }) {
  const tab = useStore((s) => s.inspectorTab)
  const setTab = useStore((s) => s.setTab)
  return (
    <div className="inspector" style={{ borderLeft: '1px solid var(--line)', background: 'rgba(8,13,22,.55)', backdropFilter: 'blur(12px)', overflow: 'auto', padding: 14 }}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 14 }}>
        {TABS.map((t) => (
          <button key={t} className={'tab ' + (t === tab ? 'on' : '')} onClick={() => setTab(t)}>{t}</button>
        ))}
      </div>
      {tab === 'view' && <ViewTab />}
      {tab === 'genesis' && <GenesisTab />}
      {tab === 'physics' && <PhysicsTab room={room} data={data} />}
    </div>
  )
}

function Slider({ label, value, on, hint }: { label: string; value: number; on: (v: number) => void; hint?: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div className="mono" style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--muted)', marginBottom: 5 }}>
        <span>{label}</span><span className="tnum">{value.toFixed(2)}</span>
      </div>
      <input className="range" type="range" min={0} max={1} step={0.01} value={value} onChange={(e) => on(Number(e.target.value))} />
      {hint && <div className="muted" style={{ fontSize: 10.5, marginTop: 4 }}>{hint}</div>}
    </div>
  )
}

function ViewTab() {
  const vs = useStore((s) => s.viewSettings)
  const setView = useStore((s) => s.setView)
  return (
    <div>
      <p className="muted" style={{ fontSize: 12, margin: '0 0 12px' }}>表示だけを変える（物理結果は変わらない・即時反映）。</p>
      <Slider label="等値面 閾値" value={vs.threshold} on={(v) => setView({ threshold: v })} hint="この値未満の領域を隠す" />
      <Slider label="透明度" value={vs.opacity} on={(v) => setView({ opacity: v })} />
      <Slider label="発光強度" value={vs.glow} on={(v) => setView({ glow: v })} />
      <Slider label="表示品質 (LOD)" value={vs.quality} on={(v) => setView({ quality: Math.max(0.3, v) })}
        hint="低性能端末では下げる（点密度・解像度を落とす／物理解像度とは無関係）" />
    </div>
  )
}

// Honest Live Runner composer: the browser does NOT compute physics. It emits a job REQUEST that a
// Python worker (tools/run_job.py) runs from t=0 with the REAL g001 reference model, producing a
// non-official candidate room. Only knobs the run actually applies are offered.
const KNOBS = {
  noise_amplitude: { label: 'noise amplitude', min: 1e-5, max: 1e-2, log: true, def: 5e-3,
    hint: '始原の微小ノイズ振幅（構造は入れない）· 許容 1e-5–1e-2' },
  quench_duration: { label: 'quench duration', min: 0.5, max: 40, log: false, def: 8,
    hint: 'クエンチにかける時間 · 許容 0–40' },
} as const
type KnobKey = keyof typeof KNOBS

function GenesisTab() {
  const room = useStore((s) => s.currentRoom())
  const [param, setParam] = useState<KnobKey>('noise_amplitude')
  const [value, setValue] = useState<number>(KNOBS.noise_amplitude.def)
  const [seed, setSeed] = useState<number>(0)
  const [copied, setCopied] = useState(false)

  const parent = room?.room_id ?? 'room-g001-a'
  const model = room?.genesis_model
  if (model && model !== GL_MODEL) {
    return (
      <div>
        <p className="muted" style={{ fontSize: 12.5, lineHeight: 1.6 }}>
          Live Runner は現在 <b>g001 参照モデル</b>（Ginzburg–Landau クエンチ）の Room からの分岐のみ対応します。
          この Room は <span className="mono">{model}</span> なので、分岐ジョブはまだ発行できません。
        </p>
        <p className="muted" style={{ fontSize: 11.5, marginTop: 10 }}>
          別モデルの Live Runner は物理コード（solver / initial-condition）の追加を伴うため、別の物理 PR で扱います。
        </p>
      </div>
    )
  }

  const k = KNOBS[param]
  const clamped = Math.min(k.max, Math.max(k.min, value))
  const jobId = 'job-' + param.replace(/_/g, '') + '-' + fmt(clamped) + '-s' + seed
  const request = { job_id: jobId, parent_room: parent, override: { param, to: clamped }, seed }
  const reqStr = JSON.stringify(request)
  const cmd = "python tools/run_job.py --request '" + reqStr + "'"

  // slider position: log or linear
  const pos = k.log
    ? (Math.log10(clamped) - Math.log10(k.min)) / (Math.log10(k.max) - Math.log10(k.min))
    : (clamped - k.min) / (k.max - k.min)
  const fromPos = (p: number) => k.log
    ? Math.pow(10, Math.log10(k.min) + p * (Math.log10(k.max) - Math.log10(k.min)))
    : k.min + p * (k.max - k.min)

  return (
    <div>
      <p className="muted" style={{ fontSize: 12, margin: '0 0 6px', lineHeight: 1.6 }}>
        始原条件を1つ変えて、<b>新しい Room として t=0 から実計算</b>する。現在の Room は変えない。
      </p>
      <p className="mono" style={{ fontSize: 10.5, color: 'var(--warn)', margin: '0 0 12px' }}>
        ブラウザは物理を計算しません。下のコマンドを実行すると本物のモデルが回り、非公式の候補 Room が生成されます。
      </p>

      <div className="mono" style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6 }}>始原ノブ</div>
      <div style={{ display: 'flex', gap: 4, marginBottom: 12 }}>
        {(Object.keys(KNOBS) as KnobKey[]).map((kk) => (
          <button key={kk} className={'tab ' + (kk === param ? 'on' : '')}
            onClick={() => { setParam(kk); setValue(KNOBS[kk].def) }}>{KNOBS[kk].label}</button>
        ))}
      </div>

      <div style={{ marginBottom: 12 }}>
        <div className="mono" style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--muted)', marginBottom: 5 }}>
          <span>{k.label}{k.log ? ' (log)' : ''}</span><span className="tnum">{fmt(clamped)}</span>
        </div>
        <input className="range" type="range" min={0} max={1} step={0.001} value={pos}
          onChange={(e) => setValue(fromPos(Number(e.target.value)))} />
        <div className="muted" style={{ fontSize: 10.5, marginTop: 4 }}>{k.hint}</div>
      </div>

      <div style={{ marginBottom: 12 }}>
        <div className="mono" style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--muted)', marginBottom: 5 }}>
          <span>seed</span><span className="tnum">{seed}</span>
        </div>
        <input className="range" type="range" min={0} max={7} step={1} value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
      </div>

      <div style={{ borderLeft: '3px solid var(--accent)', background: 'var(--accent-dim)', borderRadius: '0 10px 10px 0', padding: '10px 12px' }}>
        <div className="mono" style={{ fontSize: 11, color: 'var(--accent)', marginBottom: 6 }}>ジョブ要求</div>
        <code className="mono" style={{ display: 'block', fontSize: 10.5, whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: 'var(--ink)', marginBottom: 8 }}>{cmd}</code>
        <button className="lens" style={{ color: 'var(--accent)', borderColor: 'rgba(79,227,224,.4)' }}
          onClick={() => { copy(cmd); setCopied(true); window.setTimeout(() => setCopied(false), 1400) }}>
          {copied ? '✓ コピーしました' : '⧉ コマンドをコピー'}
        </button>
        <div className="muted" style={{ fontSize: 10.5, marginTop: 8, lineHeight: 1.5 }}>
          結果は <span className="mono">rooms/candidates/{'room-' + parent.replace('room-', '') + '-' + jobId}</span> に、
          記録された場つきで生成されます。<b>official ではなく</b>、full-3D 昇格・格子収束は別段階です。
        </div>
      </div>
    </div>
  )
}

function fmt(v: number): string {
  if (v !== 0 && (Math.abs(v) < 1e-3 || Math.abs(v) >= 1e4)) return v.toExponential(2).replace('e', 'e')
  return String(Math.round(v * 1e4) / 1e4)
}

function copy(text: string) {
  try { navigator.clipboard?.writeText(text) } catch { /* clipboard blocked in offline embeds; text is visible to select */ }
}

function PhysicsTab({ room, data }: { room: Room; data: RoomData }) {
  const tier = useStore((s) => s.physicsTier)
  const setTier = useStore((s) => s.setPhysicsTier)
  const measured = room.measured_by || {}
  const status = room.physics_status || {}
  return (
    <div>
      <div style={{ display: 'flex', gap: 4, marginBottom: 12 }}>
        {[1, 2, 3].map((n) => (
          <button key={n} className={'tab ' + (tier === n ? 'on' : '')} onClick={() => setTier(n as 1 | 2 | 3)}>Lv{n}</button>
        ))}
      </div>
      {tier === 1 && (
        <div>
          <span className="badge b-official">物理的に確認済み</span>
          <p style={{ fontSize: 14, marginTop: 12 }}>ほぼ一様な始原状態から、<b>{LEVEL_TEXT[room.reached_level ?? 0]}</b>。完成した構造は初期状態に入れていません。</p>
        </div>
      )}
      {tier === 2 && (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 8 }}>
          {Object.entries(status).map(([k, v]) => (
            <li key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span className="muted">{k}</span>
              <span style={{ color: v === 'passed' ? 'var(--official)' : 'var(--warn)' }}>{v === 'passed' ? '✓ passed' : v}</span>
            </li>
          ))}
        </ul>
      )}
      {tier === 3 && (
        <div>
          {Object.entries(measured).map(([k, v]) => (
            <div className="kv" key={k}><span>{k}</span><span className="v tnum">{typeof v === 'number' ? v : String(v)}</span></div>
          ))}
          <div className="kv"><span>lenses ↔ measured</span><span className="v">{(data.manifest?.lenses || []).length}</span></div>
          {(data.manifest?.lenses || []).map((l) => (
            <div className="kv" key={l.lens}><span>{l.lens}</span><span className="v">{l.source.field} [{l.source.unit}]</span></div>
          ))}
          <div className="muted" style={{ fontSize: 10.5, marginTop: 10 }}>
            render-manifest: data_source={data.manifest?.data_source} · changes_physics=false · decorative_particles=false
          </div>
        </div>
      )}
    </div>
  )
}
