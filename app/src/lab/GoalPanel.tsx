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
interface MapNode { id: string; parent: string | null; kind: string; text: string; by: string; universe: string | null; status: string; at: string; plain?: string }
interface Goal {
  id: string; title: string; question: string; whites: string[]; criteria: Criterion[]
  budget: Record<string, number>; researchers: Researcher[]; status: string; nodes: MapNode[]
  spent: Record<string, number>; hypothesis?: string | null; sweeps?: Sweep[]
}
interface Variant {
  seed: number; knobs: Record<string, number>; met: number; all_met: boolean; diverged: boolean; label: string
  sha256: string | null; t: number; last: Record<string, number | null>
}
interface Sweep { id: string; at: string; by: string; white: string; why: string; plain: string; frames: number; variants: Variant[] }
interface Hypothesis {
  id: string; title: string; idea: string; question: string; measure: string; falsify: string; put_in: string
  status: 'ready' | 'needs'; needs: string
}
interface EvalRow { metric: string; op: string; value: number; hold: number; met: boolean; longest: number; holding_now: number | null; last: number | null }
interface ResearcherState {
  name: string; model: string; focus: string; state: string; reason: string; owned: string[]; usd: number
  tokens: { input: number; output: number }; transcript: { at: string; kind: string; text: string }[]
}
interface GoalView {
  goal: Goal; evaluation: { met: boolean; universes: { universe: string; label: string; white: string; t: number; criteria: EvalRow[]; all_met: boolean }[] }
  now: { at: string; actor: string; what: string; universe: string | null }[]; over_budget: string | null
  researchers: ResearcherState[]; plain: string[]
}

const R_STATE: Record<string, string> = {
  starting: '準備中', running: '研究中', finished: '終えた', stopped: '止めた', over_budget: '上限で停止', error: 'エラー',
}
const T_KIND: Record<string, string> = { text: '', tool: '▶ ', result: '　↳ ', system: '' }

function Researchers({ view, onStop }: { view: GoalView; onStop: (name: string) => void }) {
  const [open, setOpen] = useState<string | null>(null)
  const configured = view.goal.researchers.length ? view.goal.researchers.map((r) => r.name) : ['研究員1']
  const live = new Map(view.researchers.map((r) => [r.name, r]))
  return (
    <div className="lab-section">
      <div className="eyebrow" title="ゴールの範囲・予算の中だけで、自分で宇宙を作って試す">AI の研究員</div>
      {configured.map((name) => {
        const r = live.get(name)
        return (
          <div key={name} className="lab-researcher">
            <div className="lab-row">
              <b>{name}</b>
              <span className={'lab-badge rs-' + (r?.state ?? 'idle')} title={r?.reason}>{r ? R_STATE[r.state] ?? r.state : 'まだ'}</span>
              <span style={{ flex: 1 }} />
              {r?.state === 'running' && <button className="lab-mini" onClick={() => onStop(name)}>■ 止める</button>}
              {r && <button className="lab-mini" onClick={() => setOpen(open === name ? null : name)}>{open === name ? '閉じる' : 'やりとり'}</button>}
            </div>
            {open === name && r && (
              <>
                <div className="mono muted lab-note">{r.model || '中心の model'}・${r.usd.toFixed(3)}・{r.tokens.input + r.tokens.output} tok・宇宙 {r.owned.length}{r.reason ? `・${r.reason}` : ''}</div>
                <div className="lab-transcript">
                  {r.transcript.slice(-60).map((e, i) => (
                    <div key={i} className={'lab-tr tr-' + e.kind}><span className="mono muted">{e.at}</span> {T_KIND[e.kind]}{e.text}</div>
                  ))}
                </div>
              </>
            )}
          </div>
        )
      })}
    </div>
  )
}

const STATUS_LABEL: Record<string, string> = { draft: '下書き', running: '進行中', paused: '止めている', done: '終了', met: '条件を満たした（測定）' }
const NODE_LABEL: Record<string, string> = { todo: '未着手', doing: '進行中', met: '満たした', not_met: '満たさない', ceiling: '天井', info: '' }
const KIND_LABEL: Record<string, string> = { question: '問い', attempt: '試した', note: 'メモ', result: '結果' }

/** How many criteria the closest universe meets (for the one-line verdict). */
function best(view: GoalView): number {
  return Math.max(0, ...view.evaluation.universes.map((u) => u.criteria.filter((c) => c.met).length))
}

const BUDGET: [string, string, string][] = [['universes', 'max_universes', '宇宙'], ['steps', 'max_steps', 'ステップ'], ['usd', 'max_usd', 'USD'], ['minutes', 'max_minutes', '分']]

/** One bar for the budget (the most used of the four); the numbers are folded away. */
function Budget({ goal }: { goal: Goal }) {
  const parts = BUDGET.map(([k, lim, label]) => ({ label, used: goal.spent[k] ?? 0, max: goal.budget[lim] ?? 0 }))
  const frac = Math.min(1, Math.max(0, ...parts.map((p) => (p.max ? p.used / p.max : 0))))
  return (
    <details className="lab-fold lab-budget">
      <summary>予算 <span className="lab-bar"><i style={{ width: `${Math.round(frac * 100)}%` }} className={frac > 0.85 ? 'hi' : ''} /></span> {Math.round(frac * 100)}%</summary>
      <div className="mono muted lab-note">
        {parts.map((p) => `${p.label} ${p.label === 'USD' ? p.used.toFixed(3) : p.label === '分' ? p.used.toFixed(1) : Math.round(p.used)}/${p.max}`).join('・')}
        {goal.whites.length ? `　白: ${goal.whites.join(', ')}` : '　白: すべて'}
      </div>
    </details>
  )
}

/** やさしい説明: sentences made from the lab's own numbers (always there), plus an optional AI rephrasing. */
function PlainCard({ gid, lines, onError }: { gid: string; lines: string[]; onError: (e: unknown) => void }) {
  const [ai, setAi] = useState<{ text: string; model: string } | null>(null)
  const [busy, setBusy] = useState(false)
  useEffect(() => { setAi(null) }, [gid])
  const ask = () => {
    setBusy(true)
    api<{ text: string; model: string }>(`goals/${gid}/explain`, { method: 'POST', body: {} })
      .then(setAi).catch(onError).finally(() => setBusy(false))
  }
  return (
    <div className="lab-plain">
      <div className="eyebrow">やさしい説明</div>
      {lines.map((l, i) => <p key={i}>{l}</p>)}
      {ai && <div className="lab-plain-ai"><p>{ai.text}</p><div className="mono muted lab-note">AI（{ai.model}）が上の説明を言いかえたもの</div></div>}
      <button className="lab-mini" disabled={busy} onClick={ask}>{busy ? '考えています…' : 'AI にもっとやさしく説明してもらう'}</button>
    </div>
  )
}

/** 「まとめて試した」: each sweep, best first; any variant can be put in a tank (it runs the same from t=0). */
function Sweeps({ goal, onTank }: { goal: Goal; onTank: (white: string, v: Variant) => void }) {
  const list = goal.sweeps ?? []
  if (!list.length) return null
  const n = goal.criteria.length
  return (
    <details className="lab-section">
      <summary>まとめて試した結果（{list.reduce((a, s) => a + s.variants.length, 0)} 通り）</summary>
      {list.slice().reverse().map((s) => (
        <div key={s.id} className="lab-sweep">
          <div>{s.plain || s.why || `${s.white} を ${s.variants.length} 通り`} <span className="mono muted">— {s.by}・{s.id}</span></div>
          <details className="lab-fold">
            <summary>{n ? `近い順（いちばん近いもの：目安 ${n} つのうち ${s.variants[0]?.met ?? 0} つ）` : '一覧'}</summary>
            {s.variants.slice(0, 12).map((v, i) => (
              <div key={i} className={'lab-row lab-variant' + (v.all_met ? ' ok' : '')}>
                <span className="mono lab-grow">{v.all_met ? '✓ ' : ''}{v.label}{v.diverged ? '（発散）' : ''}</span>
                {n > 0 && <span className="mono muted">{v.met}/{n}</span>}
                {!v.diverged && <button className="lab-mini" onClick={() => onTank(s.white, v)}>水槽に出す</button>}
              </div>
            ))}
          </details>
        </div>
      ))}
    </details>
  )
}

function HypothesisBody({ h }: { h: Hypothesis }) {
  return (
    <div className="lab-hyp-body">
      <p>{h.idea}</p>
      <p><b>問い</b> {h.question}</p>
      <p><b>測り方</b> {h.measure}</p>
      <p><b>反証になること</b> {h.falsify}</p>
      <p><b className="aq-put">置いたもの</b> {h.put_in}</p>
      {h.needs && <p><b>まだ足りないもの</b> {h.needs}</p>}
    </div>
  )
}

/** 「仮説から選ぶ」: research/hypotheses.json. A ready hypothesis becomes a goal with one press. */
function Hypotheses({ list, open, onPick }: { list: Hypothesis[]; open: boolean; onPick: (id: string) => void }) {
  if (!list.length) return null
  return (
    <details className="lab-section" open={open || undefined}>
      <summary>仮説から選ぶ（{list.filter((h) => h.status === 'ready').length} 件すぐ始められる）</summary>
      {list.map((h) => (
        <div key={h.id} className={'lab-hyp' + (h.status === 'ready' ? '' : ' off')}>
          <div className="lab-row">
            <b className="mono">{h.id}</b> <span className="lab-grow">{h.title}</span>
            {h.status === 'ready'
              ? <button className="lab-mini" onClick={() => onPick(h.id)}>ゴールにする</button>
              : <span className="lab-badge" title={h.needs}>準備中</span>}
          </div>
          <details className="lab-fold">
            <summary>中身</summary>
            <HypothesisBody h={h} />
          </details>
        </div>
      ))}
    </details>
  )
}

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
  const [edit, setEdit] = useState<string | null>(null)
  const node = (n: MapNode, depth: number): JSX.Element => (
    <div key={n.id}>
      <div className={'lab-mapnode st-' + n.status} style={{ marginLeft: depth * 14 }}
        title={NODE_LABEL[n.status] || undefined} onClick={() => setEdit(edit === n.id ? null : n.id)}>
        <span className="mono muted">{KIND_LABEL[n.kind]}</span> {n.plain || n.text}
        <span className="mono muted lab-by"> — {n.by === 'you' ? 'うえきさん' : n.by}</span>
        {edit === n.id && n.plain && <div className="mono muted lab-note">くわしく：{n.text}</div>}
        {edit === n.id && (
          <span className="lab-node-edit" onClick={(e) => e.stopPropagation()}>
            <select className="lab-mini" value={n.status} onChange={(e) => onStatus(n.id, e.target.value)} aria-label="状態">
              {Object.keys(NODE_LABEL).map((s) => <option key={s} value={s}>{NODE_LABEL[s] || '—'}</option>)}
            </select>
            <button className="lab-mini" onClick={() => setParent(n.id)}>↳ この下に書く</button>
          </span>
        )}
      </div>
      {kids(n.id).map((c) => node(c, depth + 1))}
    </div>
  )
  return (
    <div className="lab-section">
      <div className="eyebrow" title="ゴール → 問い → 試したこと → 結果">マップ</div>
      <div className="lab-mapnode root"><b>◎ {view.goal.title}</b></div>
      {kids(null).map((n) => node(n, 1))}
      <details className="lab-fold" open={parent ? true : undefined}>
        <summary>＋ マップに書く</summary>
      <div className="lab-row">
        <select className="aq-select" value={kind} onChange={(e) => setKind(e.target.value)}>
          {['question', 'note', 'result'].map((k) => <option key={k} value={k}>{KIND_LABEL[k]}</option>)}
        </select>
        <input className="lab-note-input lab-grow" value={text} onChange={(e) => setText(e.target.value)}
          placeholder={parent ? `${parent} の下に` : 'ゴールの下に'} />
        <button className="tbtn" disabled={!text.trim()} onClick={() => { onAdd(kind, text, parent); setText(''); setParent(null) }}>足す</button>
      </div>
      </details>
    </div>
  )
}

export default function GoalPanel({ whites, models, activeGoal, setActiveGoal, onError, onUniverse }: {
  whites: { id: string; title: string }[]; models: ModelEntry[]
  activeGoal: string | null; setActiveGoal: (id: string | null) => void; onError: (e: unknown) => void
  onUniverse?: () => void
}) {
  const [list, setList] = useState<Goal[]>([])
  const [hyps, setHyps] = useState<Hypothesis[]>([])
  useEffect(() => { api<{ hypotheses: Hypothesis[] }>('goals/hypotheses').then((d) => setHyps(d.hypotheses)).catch(() => {}) }, [])
  const fromHypothesis = (id: string) => api<Goal>('goals', { method: 'POST', body: { hypothesis: id } })
    .then((g) => { loadList(); setActiveGoal(g.id) }).catch(onError)
  const [view, setView] = useState<GoalView | null>(null)
  const loadList = useCallback(() => api<{ goals: Goal[] }>('goals').then((d) => setList(d.goals)).catch(onError), [onError])
  const load = useCallback(() => {
    if (!activeGoal) { setView(null); return }
    api<GoalView>('goals/' + activeGoal).then(setView).catch(onError)
  }, [activeGoal, onError])
  useEffect(() => { loadList() }, [loadList])
  useEffect(() => { load(); const id = setInterval(load, 3000); return () => clearInterval(id) }, [load])

  const [startNote, setStartNote] = useState<string | null>(null)
  const setStatus = (status: string) => api<{ started?: { name: string; state: string; reason: string }[] }>('goals/' + activeGoal, { method: 'POST', body: { status } })
    .then((r) => {
      const bad = (r.started ?? []).filter((x) => x.state === 'error')
      setStartNote(bad.length ? bad.map((x) => `${x.name}: ${x.reason}`).join(' / ') : null)
      load(); loadList()
    }).catch(onError)
  const toTank = (white: string, v: Variant) =>
    api('universes', { method: 'POST', body: { white, seed: v.seed, knobs: v.knobs, goal: activeGoal } })
      .then(() => { onUniverse?.(); load() }).catch(onError)
  const stopOne = (name: string) => api(`goals/${activeGoal}/researchers/${encodeURIComponent(name)}/stop`, { method: 'POST', body: {} }).then(load).catch(onError)
  const addNode = (kind: string, text: string, parent: string | null) =>
    api(`goals/${activeGoal}/nodes`, { method: 'POST', body: { kind, text, parent } }).then(load).catch(onError)
  const nodeStatus = (nid: string, status: string) =>
    api(`goals/${activeGoal}/nodes/${nid}`, { method: 'POST', body: { status } }).then(load).catch(onError)

  return (
    <div>
      <div className="lab-row">
        <select className="aq-select lab-grow" value={activeGoal ?? ''} onChange={(e) => setActiveGoal(e.target.value || null)}
          title="ゴールを選んでいる間に作った宇宙・分岐は、マップに「試した」として入ります">
          <option value="">（ゴールなしで自由に）</option>
          {list.map((g) => <option key={g.id} value={g.id}>{g.title}（{STATUS_LABEL[g.status] ?? g.status}）</option>)}
        </select>
      </div>

      {view && (
        <>
          <PlainCard gid={view.goal.id} lines={view.plain ?? []} onError={onError} />
          <div className="lab-section">
            <div className="lab-goal-head"><b>{view.goal.title}</b> <span className={'lab-badge st-' + view.goal.status}>{STATUS_LABEL[view.goal.status] ?? view.goal.status}</span></div>
            {view.goal.question && <p className="lab-note">{view.goal.question}</p>}
            {view.goal.hypothesis && hyps.find((h) => h.id === view.goal.hypothesis) && (
              <details className="lab-fold">
                <summary>仮説 {view.goal.hypothesis} の中身（反証・置いたもの）</summary>
                <HypothesisBody h={hyps.find((h) => h.id === view.goal.hypothesis)!} />
              </details>
            )}
            <Budget goal={view.goal} />
            {view.over_budget && <div className="lab-error">{view.over_budget}</div>}
            <div className="lab-row">
              {view.goal.status !== 'running'
                ? <button className="tbtn pri" onClick={() => setStatus('running')}>始める（研究員が動き出す）</button>
                : <button className="tbtn" onClick={() => setStatus('paused')}>■ 全員止める</button>}
              <button className="tbtn" onClick={() => setStatus('done')}>終える</button>
            </div>
            {startNote && <div className="lab-error">始められなかった研究員: {startNote}</div>}
          </div>
          <div className="lab-section">
            <div className="eyebrow" title="測定値だけで判定する">判定</div>
            <div className={'lab-verdict' + (view.evaluation.met ? ' ok' : '')}>
              {!view.goal.criteria.length ? '条件がありません'
                : view.evaluation.met ? `✓ 条件を満たした宇宙: ${view.evaluation.universes.filter((u) => u.all_met).map((u) => u.label).join(', ')}`
                  : view.evaluation.universes.length ? `まだ（いちばん近い宇宙で ${best(view)} / ${view.goal.criteria.length} 条件）` : 'まだ宇宙がありません'}
            </div>
            {view.goal.criteria.length > 0 && view.evaluation.universes.length > 0 && (
            <details className="lab-fold">
              <summary>宇宙ごとの数字</summary>
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
            </details>
            )}
          </div>
          <div className="lab-section">
            <div className="eyebrow">いまやっていること</div>
            {!view.now.length && <p className="muted lab-note">まだ誰も動いていません。</p>}
            {view.now.map((a) => (
              <div key={a.actor} className="lab-now"><b>{a.actor === 'you' ? 'うえきさん' : a.actor}</b> <span className="mono muted">{a.at.slice(11)}</span> {a.what}</div>
            ))}
          </div>
          <Researchers view={view} onStop={stopOne} />
          <Sweeps goal={view.goal} onTank={toTank} />
          <MapTree view={view} onAdd={addNode} onStatus={nodeStatus} />
        </>
      )}
      <Hypotheses list={hyps} open={!activeGoal} onPick={fromHypothesis} />
      <NewGoal whites={whites} models={models} onCreated={(g) => { loadList(); setActiveGoal(g.id) }} onError={onError} />
    </div>
  )
}
