import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type UniverseInfo, type WhiteSpec } from './api'
import type { ModelEntry } from './GoalPanel'
import ObservePanel from './ObservePanel'

interface Role { role: string; label: string; provider: string | null; model: string; available: boolean; reason: string }
interface Msg {
  id: number; who: string; label: string; model: string; text: string; done: boolean; kind: string
  usage: { input_tokens: number; output_tokens: number } | null; usd: number; at: string
}
interface Proposal {
  id: number; source: string; mode?: 'initial'; parent: string; parent_label: string; white: string; at_step: number
  set: Record<string, number>; perturb: { name: string; args: Record<string, number> } | null
  seed?: number; base_seed?: number; base_knobs?: Record<string, number>; knobs?: Record<string, number>
  why: string; predict: string; put_in: string; status: 'open' | 'tried' | 'dismissed'; child: string | null
}
interface CouncilState {
  roles: Role[]; busy: boolean; spent_today: number; limit_usd: number; bridge: boolean
  messages: Msg[]; proposals: Proposal[]
}
const WHO_COLOR: Record<string, string> = {
  core: 'var(--accent)', vision: 'var(--candidate)', second_view: 'var(--warn)', you: 'var(--ink)',
  'claude-code': 'var(--official)', system: 'var(--muted)',
}

export default function GuidePanel({ universes, selected, whites, models, onError, onBranched }: {
  universes: UniverseInfo[]; selected: string | null; whites: WhiteSpec[]; models: ModelEntry[]
  onError: (e: unknown) => void; onBranched: (id: string) => void
}) {
  const [state, setState] = useState<CouncilState | null>(null)
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [text, setText] = useState('')
  const [all, setAll] = useState(false)
  const [sending, setSending] = useState(false)
  const [trying, setTrying] = useState<number | null>(null)
  const [withObservation, setWithObservation] = useState(true)
  const [notice, setNotice] = useState('')
  const since = useRef(0)
  const chatBox = useRef<HTMLDivElement>(null)
  const form = useRef<HTMLTextAreaElement>(null)
  const current = universes.find((u) => u.id === selected)
  const white = whites.find((w) => w.id === current?.white)
  const ids = all ? universes.map((u) => u.id) : current ? [current.id] : []

  const poll = useCallback(() => {
    return api<CouncilState>('council?since=' + since.current).then((s) => {
      setState(s)
      if (s.messages.length) {
        setMsgs((old) => {
          const byId = new Map(old.map((m) => [m.id, m]))
          for (const m of s.messages) byId.set(m.id, m)
          const result = [...byId.values()].sort((a, b) => a.id - b.id)
          since.current = Math.max(since.current, ...result.filter((m) => m.done).map((m) => m.id))
          return result
        })
      }
    })
  }, [])
  const active = sending || !!state?.busy || msgs.some((m) => !m.done)
  useEffect(() => {
    poll().catch(onError)
    const timer = setInterval(() => poll().catch(onError), active ? 900 : 4000)
    return () => clearInterval(timer)
  }, [poll, active, onError])
  useEffect(() => {
    const box = chatBox.current
    if (box) box.scrollTop = box.scrollHeight
  }, [msgs])

  const send = async () => {
    if (active || !text.trim() || !ids.length) return
    setSending(true)
    setNotice('')
    try {
      const observe = withObservation || !msgs.length
      await api(observe ? 'council/look' : 'council/chat', {
        method: 'POST', body: observe ? { ids, text: text.trim() } : { text: text.trim() },
      })
      setText('')
      await poll()
    } catch (e) { onError(e) } finally { setSending(false) }
  }
  const tryIt = async (p: Proposal) => {
    if (trying !== null) return
    setTrying(p.id)
    try {
      const result = await api<Proposal>(`proposals/${p.id}/try`, { method: 'POST' })
      if (result.child) {
        onBranched(result.child)
        setNotice(`新しい実験を表示しました。${p.mode === 'initial' ? '時刻0から計算しています。' : '途中介入として記録しました。'}画面の実測値と「比較」タブで違いを確認できます。`)
      }
      await poll()
    } catch (e) { onError(e) } finally { setTrying(null) }
  }
  const open = state?.proposals.filter((p) => p.status === 'open') ?? []
  const suggestions = white ? [
    white.knobs.find((k) => k.kind === 'start') ? `始め方の「${white.knobs.find((k) => k.kind === 'start')!.label}」を変えたらどうなる？` : 'seed だけ変えたら、どんな違いが出る？',
    white.knobs.find((k) => k.kind === 'law') ? `「${white.knobs.find((k) => k.kind === 'law')!.label}」が今の半分だったら？` : '今と違う初期条件で、時刻0から比べたい',
  ] : []

  return (
    <div className="lab-guide">
      <div className="lab-assistant-heading"><span className="lab-ai-mark">✳</span><div><h2>問いから、次の実験へ。</h2><p>いま見ている場を、AIと一緒に考える。</p></div></div>
      <div className="lab-question-flow" aria-label="実験の進め方">
        <span className={!active && !open.length ? 'on' : ''}>01 質問する</span><span className={active ? 'on' : ''}>02 条件をつくる</span><span className={open.length ? 'on' : ''}>03 動かして見る</span>
      </div>
      <details className="lab-ai-settings lab-fold">
        <summary><span className={'lab-connection ' + (state && !state.bridge ? 'connected' : '')} />
          {state ? state.bridge ? 'AI未接続 · 接続設定 / 外部AIに渡す' : 'AI接続済み · モデル / 費用' : 'AIの接続を確認中…'}</summary>
        <div className="lab-roles">
          {state?.roles.map((r) => <label key={r.role} className={'lab-role' + (r.available ? ' on' : '')}>
            <span>{r.label}</span>
            <select className="lab-mini" aria-label={`${r.label}のモデル`} value={models.find((m) => m.provider === r.provider && m.model === r.model)?.key ?? ''}
              onChange={(e) => api('council/select', { method: 'POST', body: { role: r.role, key: e.target.value } }).then(poll).catch(onError)}>
              <option value="">（なし）</option>
              {models.filter((m) => r.role !== 'vision' || m.images).map((m) => <option key={m.key} value={m.key}>{m.label}{m.available ? '' : '（未設定）'}</option>)}
            </select>
            {!r.available && <div className="lab-note muted">{r.reason || '未設定'}</div>}
          </label>)}
        </div>
        {state && <p className="lab-note muted">今日の費用 ${state.spent_today.toFixed(3)} / 上限 ${state.limit_usd.toFixed(2)}</p>}
        <p className="lab-note muted">AIには選んだ実験の画像・測定値・レシピと質問を渡します。キーはサーバー側で設定します。未接続の場合は観測パケットを保存し、リポジトリの外部AI（/guide）から提案を受け取れます。</p>
      </details>
      <div className="lab-question-context">
        <span className="eyebrow">CONTEXT</span>
        <b>{ids.length ? all ? `${ids.length}個の実験を比較` : `${current?.label} · ${white?.title ?? current?.white}` : 'まず場を選んで実験を始めましょう'}</b>
        {universes.length > 1 && <label><input type="checkbox" checked={all} onChange={(e) => setAll(e.target.checked)} />すべての実験をAIに見せる</label>}
      </div>
      {!msgs.length && <div className="lab-ai-welcome"><span>「これって、こうしたらどうなる？」</span>
        <p>気になったことを、そのままどうぞ。AIが変更する入力を提案します。結果は、実際に計算して確かめます。</p>
        {suggestions.map((q) => <button className="lab-question-example" key={q} onClick={() => { setText(q); form.current?.focus() }}>{q}<span>↗</span></button>)}
      </div>}
      <div className="lab-chat" ref={chatBox} role="log" aria-label="AIとの対話" aria-live="polite" aria-relevant="additions">
        {msgs.map((m) => <article key={m.id} className={'lab-msg who-' + m.who}>
          <div className="lab-msg-head"><b style={{ color: WHO_COLOR[m.who] ?? 'var(--ink)' }}>{m.label}</b>
            <span className="mono muted"> {m.at}{m.done ? '' : ' · 考え中'}</span></div>
          <div className="lab-msg-text">{m.text}</div>
        </article>)}
      </div>
      {active && <div className="lab-thinking" role="status"><i />観測を読み、条件を考えています…</div>}
      {state && state.proposals.length > 0 && <section className="lab-proposals">
        <div className="lab-section-title"><h3>試せる入力</h3><span>{open.length}件の提案</span></div>
        {state.proposals.filter((p) => p.status !== 'dismissed').map((p) => {
          const w = whites.find((x) => x.id === p.white)
          return <article key={p.id} className={'lab-card st-' + p.status}>
            <div className="lab-card-kicker" title={`提案元: ${p.source}`}>EXPERIMENT {String(p.id).padStart(2, '0')}{p.source !== 'core' && <small>{p.source}</small>}<span>{p.mode === 'initial' ? 't=0 から新規計算' : '途中介入の分岐'}</span></div>
            <h3>{p.why || `${p.parent_label} の条件を変えて試す`}</h3>
            <div className="lab-note muted">{p.parent_label} の{p.mode === 'initial' ? '初期レシピを継承。途中の介入は引き継ぎません。' : `現在の状態から分岐。提案時 step=${p.at_step}、実行時の状態を使います。`}</div>
            <dl className="lab-input-diff">
              {Object.entries(p.set).map(([k, v]) => <div key={k}><dt>{w?.knobs.find((x) => x.name === k)?.label ?? k}</dt><dd><span>{p.base_knobs?.[k] ?? '変更前'}</span> → <b>{v}</b></dd></div>)}
              {p.mode === 'initial' && <div><dt>seed</dt><dd>{p.base_seed} → <b>{p.seed}</b></dd></div>}
              {p.perturb && <div><dt>手で加えるもの</dt><dd>{w?.perturbs.find((x) => x.name === p.perturb?.name)?.label ?? p.perturb.name}</dd></div>}
            </dl>
            {p.predict && <p className="lab-prediction"><b>予想 · 未検証</b>{p.predict}</p>}
            {p.put_in && <p className="lab-note muted">置くもの：{p.put_in}</p>}
            {p.status === 'open' ? <div className="lab-row">
              <button className="tbtn pri" disabled={trying !== null} onClick={() => tryIt(p)}>{trying === p.id ? '計算を準備中…' : p.mode === 'initial' ? '▶ この条件で動かす' : '▶ 途中介入として試す'}</button>
              <button className="tbtn" disabled={trying !== null} onClick={() => api(`proposals/${p.id}/dismiss`, { method: 'POST' }).then(poll).catch(onError)}>見送る</button>
            </div> : <div className="lab-tried">✓ 実行済み <button className="tbtn" onClick={() => p.child && onBranched(p.child)}>実験 {universes.find((u) => u.id === p.child)?.label ?? p.child} を選ぶ ↗</button></div>}
            {p.mode === 'initial' && <details className="lab-fold"><summary>生成された入力（再現用）</summary><pre className="lab-pre">{JSON.stringify({ white: p.white, seed: p.seed, knobs: p.knobs, events: [] }, null, 2)}</pre></details>}
          </article>
        })}
      </section>}
      {notice && <div className="lab-notice" role="status">{notice}</div>}
      <form className="lab-compose" onSubmit={(e) => { e.preventDefault(); void send() }}>
        <label htmlFor="lab-question">気になったことを質問する</label>
        <textarea id="lab-question" ref={form} value={text} onChange={(e) => setText(e.target.value)} rows={3} maxLength={8000}
          placeholder="例えば、最初のゆらぎがもっと小さかったら？"
          onKeyDown={(e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !e.nativeEvent.isComposing) { e.preventDefault(); void send() } }} />
        <label className="lab-observe-toggle"><input type="checkbox" checked={withObservation} onChange={(e) => setWithObservation(e.target.checked)} />最新の可視化と測定値を添える</label>
        <button className="tbtn pri lab-send" type="submit" disabled={active || !ids.length || !text.trim() || !state}>
          {active ? 'AIが考えています…' : state?.bridge ? '観測を保存してAIに渡す ↗' : 'AIに質問して条件をつくる ↗'}</button>
        <p className="lab-note muted">{state?.bridge ? '現在AIは未接続です。保存だけでは返答は生成されません。' : '提案を動かすかは、入力を見てから選べます。'}</p>
      </form>
      <details className="lab-section lab-fold"><summary>AIに渡す観測データを確認</summary>
        <ObservePanel ids={ids} onError={onError} />
      </details>
    </div>
  )
}
