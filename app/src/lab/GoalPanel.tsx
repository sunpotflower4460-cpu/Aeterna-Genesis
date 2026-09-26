import { useCallback, useEffect, useState } from 'react'
import { api } from './api'

// Goals: a question + conditions that MEASUREMENTS decide + what is allowed (whites, budget, researchers),
// the map of what was tried, and who is doing what now. The lab only reports whether the chosen numbers
// were met; whether that means anything is for people (and /audit) to decide.

export interface ModelEntry {
  key: string; label: string; provider: string; model: string; available: boolean; reason: string
  tools: boolean; images: boolean; video: boolean
}
interface Criterion { metric: string; op: string; value: number; hold: number; label?: string }
interface Researcher { name: string; model: string; focus: string }
interface MapNode { id: string; parent: string | null; kind: string; text: string; by: string; universe: string | null; status: string; at: string }
interface Goal {
  id: string; title: string; question: string; whites: string[]; criteria: Criterion[]
  budget: Record<string, number>; researchers: Researcher[]; status: string; nodes: MapNode[]
  spent: Record<string, number>
}
interface EvalRow { metric: string; op: string; value: number; hold: number; met: boolean; longest: number; holding_now: number | null; last: number | null }
interface GoalView {
  goal: Goal; evaluation: { met: boolean; universes: { universe: string; label: string; white: string; t: number; criteria: EvalRow[]; all_met: boolean }[] }
  now: { at: string; actor: string; what: string; universe: string | null }[]; over_budget: string | null
}

const STATUS_LABEL: Record<string, string> = { draft: '下書き', running: '進行中', paused: '止めている', done: '終了', met: '条件を満たした（測定）' }
const NODE_LABEL: Record<string, string> = { todo: '未着手', doing: '進行中', met: '満たした', not_met: '満たさない', ceiling: '天井', info: '' }
const KIND_LABEL: Record<string, string> = { question: '問い', attempt: '試した', note: 'メモ', result: '結果' }

function NewGoal({ whites, models, onCreated, onError }: {
  whites: { id: string; title: string }[]; models: ModelEntry[]; onCreated: (g: Goal) => void; onError: (e: unknown) => void
}) {
  const [title, setTitle] = useState('')
  const [question, setQuestion] = useState('')
  const [ws, setWs] = useState<string[]>([])
  const [metrics, setMetrics] = useState<Record<string, string[]>>({})
  const [crit, setCrit] = useState<Criterion[]>([])
  const [budget, setBudget] = useState({ max_universes: 3, max_steps: 2000000, max_usd: 1, max_minutes: 30 })
  const [rs, setRs] = useState<Researcher[]>([])
  useEffect(() => {
    if (!ws.length) { setMetrics({}); return }
    api<{ metrics: Record<string, string[]> }>('goals/metrics?whites=' + ws.join(',')).then((d) => setMetrics(d.metrics)).catch(onError)
  }, [ws.join(','), onError]) // eslint-disable-line react-hooks/exhaustive-deps
  const names = [...new Set(Object.values(metrics).flat())]
  const toolModels = models.filter((m) => m.tools)
  const create = () => api<Goal>('goals', { method: 'POST', body: { title, question, whites: ws, criteria: crit, budget, researchers: rs } })
    .then((g) => { onCreated(g); setTitle(''); setQuestion(''); setCrit([]); setRs([]) }).catch(onError)
  return (
    <details className="lab-section">
      <summary>＋ 新しいゴール</summary>
      <input className="lab-note-input" placeholder="ゴールの名前（例：一つの白で、まとまりと自分で動く）" value={title} onChange={(e) => setTitle(e.target.value)} />
      <textarea className="lab-note-input" rows={2} placeholder="問い（ことばで）" value={question} onChange={(e) => setQuestion(e.target.value)} />
      <div className="eyebrow">使ってよい白</div>
      <div className="lab-row">
        {whites.map((w) => (
          <label key={w.id} className="aq-knob mono"><input type="checkbox" checked={ws.includes(w.id)}
            onChange={(e) => setWs((o) => e.target.checked ? [...o, w.id] : o.filter((x) => x !== w.id))} />{w.id}</label>
        ))}
      </div>
      <div className="eyebrow">達成の条件（測定値で判定・全部を同じ宇宙で同時に）</div>
      {crit.map((c, i) => (
        <div key={i} className="lab-row lab-crit">
          <select className="aq-select" value={c.metric} onChange={(e) => setCrit((o) => o.map((x, j) => j === i ? { ...x, metric: e.target.value } : x))}>
            {names.map((n) => <option key={n}>{n}</option>)}
          </select>
          <select className="aq-select" value={c.op} onChange={(e) => setCrit((o) => o.map((x, j) => j === i ? { ...x, op: e.target.value } : x))}>
            {['>', '>=', '<', '<=', '==', '!='].map((o) => <option key={o}>{o}</option>)}
          </select>
          <input className="lab-num" type="number" value={c.value} onChange={(e) => setCrit((o) => o.map((x, j) => j === i ? { ...x, value: Number(e.target.value) } : x))} />
          <span className="mono muted">を</span>
          <input className="lab-num" type="number" min={0} value={c.hold} onChange={(e) => setCrit((o) => o.map((x, j) => j === i ? { ...x, hold: Number(e.target.value) } : x))} />
          <span className="mono muted">時間続ける</span>
          <button className="tbtn" onClick={() => setCrit((o) => o.filter((_, j) => j !== i))}>×</button>
        </div>
      ))}
      <button className="tbtn" disabled={!names.length} onClick={() => setCrit((o) => [...o, { metric: names[0], op: '>', value: 0, hold: 0 }])}>条件を足す</button>
      {!names.length && <span className="muted lab-note"> 白を選ぶと、測っている量が選べます（speed は塊が 1 つのときの重心の速さ）</span>}
      <div className="eyebrow">上限</div>
      <div className="lab-row">
        {([['max_universes', '宇宙'], ['max_steps', 'ステップ'], ['max_usd', 'USD'], ['max_minutes', '分']] as const).map(([k, l]) => (
          <label key={k} className="aq-knob mono">{l}<input className="lab-num" type="number" value={budget[k]} onChange={(e) => setBudget((o) => ({ ...o, [k]: Number(e.target.value) }))} /></label>
        ))}
      </div>
      <div className="eyebrow">AI の研究員（ゴールの範囲で自分で試す・最大 3 人）</div>
      {rs.map((r, i) => (
        <div key={i} className="lab-row">
          <input className="lab-num lab-name" value={r.name} onChange={(e) => setRs((o) => o.map((x, j) => j === i ? { ...x, name: e.target.value } : x))} />
          <select className="aq-select" value={r.model} onChange={(e) => setRs((o) => o.map((x, j) => j === i ? { ...x, model: e.target.value } : x))}>
            {toolModels.map((m) => <option key={m.key} value={m.key}>{m.label}{m.available ? '' : '（未設定）'}</option>)}
          </select>
          <input className="lab-note-input" placeholder="この人の担当（例：θ を振る）" value={r.focus} onChange={(e) => setRs((o) => o.map((x, j) => j === i ? { ...x, focus: e.target.value } : x))} />
          <button className="tbtn" onClick={() => setRs((o) => o.filter((_, j) => j !== i))}>×</button>
        </div>
      ))}
      <button className="tbtn" disabled={rs.length >= 3 || !toolModels.length}
        onClick={() => setRs((o) => [...o, { name: `研究員${o.length + 1}`, model: toolModels[0]?.key ?? '', focus: '' }])}>研究員を足す</button>
      <div className="lab-row"><button className="tbtn pri" disabled={!title.trim()} onClick={create}>ゴールを作る</button></div>
    </details>
  )
}

function MapTree({ view, onAdd, onStatus }: {
  view: GoalView; onAdd: (kind: string, text: string, parent: string | null) => void; onStatus: (nid: string, status: string) => void
}) {
  const [text, setText] = useState('')
  const [kind, setKind] = useState('question')
  const [parent, setParent] = useState<string | null>(null)
  const nodes = view.goal.nodes
  const kids = (p: string | null) => nodes.filter((n) => n.parent === p)
  const node = (n: MapNode, depth: number): JSX.Element => (
    <div key={n.id}>
      <div className={'lab-mapnode st-' + n.status} style={{ marginLeft: depth * 14 }}>
        <span className="mono muted">{KIND_LABEL[n.kind]}</span> {n.text}
        <span className="mono muted"> — {n.by === 'you' ? 'うえきさん' : n.by}{NODE_LABEL[n.status] ? `・${NODE_LABEL[n.status]}` : ''}</span>
        <select className="lab-mini" value={n.status} onChange={(e) => onStatus(n.id, e.target.value)} aria-label="状態">
          {Object.keys(NODE_LABEL).map((s) => <option key={s} value={s}>{NODE_LABEL[s] || '—'}</option>)}
        </select>
        <button className="lab-mini" onClick={() => setParent(n.id)}>↳</button>
      </div>
      {kids(n.id).map((c) => node(c, depth + 1))}
    </div>
  )
  return (
    <div className="lab-section">
      <div className="eyebrow">マップ（ゴール → 問い → 試したこと → 結果）</div>
      <div className="lab-mapnode root"><b>◎ {view.goal.title}</b></div>
      {kids(null).map((n) => node(n, 1))}
      <div className="lab-row">
        <select className="aq-select" value={kind} onChange={(e) => setKind(e.target.value)}>
          {['question', 'note', 'result'].map((k) => <option key={k} value={k}>{KIND_LABEL[k]}</option>)}
        </select>
        <input className="lab-note-input lab-grow" value={text} onChange={(e) => setText(e.target.value)}
          placeholder={parent ? `${parent} の下に` : 'ゴールの下に'} />
        <button className="tbtn" disabled={!text.trim()} onClick={() => { onAdd(kind, text, parent); setText(''); setParent(null) }}>足す</button>
      </div>
    </div>
  )
}

export default function GoalPanel({ whites, models, activeGoal, setActiveGoal, onError }: {
  whites: { id: string; title: string }[]; models: ModelEntry[]
  activeGoal: string | null; setActiveGoal: (id: string | null) => void; onError: (e: unknown) => void
}) {
  const [list, setList] = useState<Goal[]>([])
  const [view, setView] = useState<GoalView | null>(null)
  const loadList = useCallback(() => api<{ goals: Goal[] }>('goals').then((d) => setList(d.goals)).catch(onError), [onError])
  const load = useCallback(() => {
    if (!activeGoal) { setView(null); return }
    api<GoalView>('goals/' + activeGoal).then(setView).catch(onError)
  }, [activeGoal, onError])
  useEffect(() => { loadList() }, [loadList])
  useEffect(() => { load(); const id = setInterval(load, 3000); return () => clearInterval(id) }, [load])

  const setStatus = (status: string) => api('goals/' + activeGoal, { method: 'POST', body: { status } }).then(() => { load(); loadList() }).catch(onError)
  const addNode = (kind: string, text: string, parent: string | null) =>
    api(`goals/${activeGoal}/nodes`, { method: 'POST', body: { kind, text, parent } }).then(load).catch(onError)
  const nodeStatus = (nid: string, status: string) =>
    api(`goals/${activeGoal}/nodes/${nid}`, { method: 'POST', body: { status } }).then(load).catch(onError)

  return (
    <div>
      <div className="lab-row">
        <select className="aq-select lab-grow" value={activeGoal ?? ''} onChange={(e) => setActiveGoal(e.target.value || null)}>
          <option value="">（ゴールなしで自由に）</option>
          {list.map((g) => <option key={g.id} value={g.id}>{g.title}（{STATUS_LABEL[g.status] ?? g.status}）</option>)}
        </select>
      </div>
      {activeGoal && <p className="muted lab-note">このゴールを選んでいる間に作った宇宙・分岐は、マップに「試した」として入ります。</p>}
      {view && (
        <>
          <div className="lab-section">
            <div className="lab-goal-head"><b>{view.goal.title}</b> <span className={'lab-badge st-' + view.goal.status}>{STATUS_LABEL[view.goal.status] ?? view.goal.status}</span></div>
            {view.goal.question && <p className="lab-note">{view.goal.question}</p>}
            <div className="mono muted lab-note">白: {view.goal.whites.join(', ') || 'すべて'} ・ 使った量: 宇宙 {view.goal.spent.universes ?? 0}/{view.goal.budget.max_universes}・
              ステップ {Math.round(view.goal.spent.steps ?? 0)}/{view.goal.budget.max_steps}・${(view.goal.spent.usd ?? 0).toFixed(3)}/{view.goal.budget.max_usd}・
              {(view.goal.spent.minutes ?? 0).toFixed(1)}/{view.goal.budget.max_minutes} 分</div>
            {view.over_budget && <div className="lab-error">{view.over_budget}</div>}
            <div className="lab-row">
              {view.goal.status !== 'running'
                ? <button className="tbtn pri" onClick={() => setStatus('running')}>始める</button>
                : <button className="tbtn" onClick={() => setStatus('paused')}>■ 止める</button>}
              <button className="tbtn" onClick={() => setStatus('done')}>終える</button>
            </div>
          </div>
          <div className="lab-section">
            <div className="eyebrow">判定（測定値だけで・{view.evaluation.met ? '条件を満たした宇宙がある' : 'まだ満たしていない'}）</div>
            {!view.goal.criteria.length && <p className="muted lab-note">条件がありません。</p>}
            {view.evaluation.universes.map((u) => (
              <div key={u.universe} className="lab-evalrow">
                <b>{u.label}</b> <span className="mono muted">{u.white} t={u.t.toFixed(1)}</span> {u.all_met ? '✓ 全部' : ''}
                {u.criteria.map((c, i) => (
                  <div key={i} className={'mono lab-crit-row ' + (c.met ? 'ok' : '')}>
                    {c.met ? '✓' : '·'} {c.metric} {c.op} {c.value}（{c.hold} 時間）: いま {c.last === null ? '—' : Number(c.last.toPrecision(4))}・最長 {c.longest}
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div className="lab-section">
            <div className="eyebrow">いまやっていること</div>
            {!view.now.length && <p className="muted lab-note">まだ誰も動いていません。</p>}
            {view.now.map((a) => (
              <div key={a.actor} className="lab-now"><b>{a.actor === 'you' ? 'うえきさん' : a.actor}</b> <span className="mono muted">{a.at.slice(11)}</span> {a.what}</div>
            ))}
          </div>
          <MapTree view={view} onAdd={addNode} onStatus={nodeStatus} />
        </>
      )}
      <NewGoal whites={whites} models={models} onCreated={(g) => { loadList(); setActiveGoal(g.id) }} onError={onError} />
    </div>
  )
}
