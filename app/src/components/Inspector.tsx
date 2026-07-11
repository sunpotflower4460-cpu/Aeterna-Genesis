import { useStore } from '../store'
import type { InspectorTab } from '../store'
import type { Room } from '../lib/types'
import type { RoomData } from '../lib/useField'
import { LEVEL_TEXT } from './ui'

const TABS: InspectorTab[] = ['view', 'genesis', 'physics']

export default function Inspector({ room, data }: { room: Room; data: RoomData }) {
  const tab = useStore((s) => s.inspectorTab)
  const setTab = useStore((s) => s.setTab)
  return (
    <div style={{ borderLeft: '1px solid var(--line)', background: 'rgba(8,13,22,.55)', backdropFilter: 'blur(12px)', overflow: 'auto', padding: 14 }}>
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
    </div>
  )
}

function GenesisTab() {
  const pending = useStore((s) => s.pendingGenesis)
  const stage = useStore((s) => s.stageGenesis)
  const discard = useStore((s) => s.discardGenesis)
  const g = pending || {}
  return (
    <div>
      <p className="muted" style={{ fontSize: 12, margin: '0 0 12px' }}>始原条件は<b>保留中</b>として貯める。現在の Room は変えず、新しい Room として t=0 から実行する。</p>
      <Slider label="noise amplitude" value={g['noise'] ?? 0.35} on={(v) => stage('noise', v)} />
      <Slider label="correlation length" value={g['correlation'] ?? 0.3} on={(v) => stage('correlation', v)} />
      <Slider label="seed (正規化)" value={g['seed'] ?? 0} on={(v) => stage('seed', v)} />
      {pending && (
        <div style={{ borderLeft: '3px solid var(--warn)', background: 'rgba(243,183,76,.06)', borderRadius: '0 10px 10px 0', padding: '10px 12px', marginTop: 8 }}>
          <div className="mono" style={{ fontSize: 11, color: 'var(--warn)', marginBottom: 4 }}>保留中の始原条件</div>
          <div className="muted" style={{ fontSize: 12 }}>この変更は時間発展へ影響します。現在の Room は変更せず、新しい Room として t=0 から実行します。</div>
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            <button className="lens" style={{ color: 'var(--accent)', borderColor: 'rgba(79,227,224,.4)', background: 'var(--accent-dim)' }}
              onClick={() => alert('Live Runner は Phase 3（非同期ジョブ）で実装予定。始原条件を変えた新 Room を t=0 から実行します。')}>
              ＋ 新しい Room として実行
            </button>
            <button className="lens" onClick={discard}>破棄</button>
          </div>
        </div>
      )}
    </div>
  )
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
