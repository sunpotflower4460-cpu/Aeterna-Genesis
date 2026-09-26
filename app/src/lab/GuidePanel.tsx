import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'
import type { ModelEntry } from './GoalPanel'

// The AI council: 見る係 (images/video, always "見た目（未測定）"), 別の視点, and the 中心 (Opus 5.5) who talks with
// you and puts proposal cards on the table. Nothing runs until you press 分岐して試す on a card.

interface Role { role: string; label: string; provider: string | null; model: string; available: boolean; reason: string }
interface Msg {
  id: number; who: string; label: string; model: string; text: string; done: boolean; kind: string
  usage: { input_tokens: number; output_tokens: number } | null; usd: number; at: string
}
interface Proposal {
  id: number; source: string; parent: string; parent_label: string; white: string; at_step: number
  set: Record<string, number>; perturb: { name: string; args: Record<string, number> } | null
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

export default function GuidePanel({ ids, models, onError, onBranched }: {
  ids: string[]; models: ModelEntry[]; onError: (e: unknown) => void; onBranched: () => void
}) {
  const [state, setState] = useState<CouncilState | null>(null)
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [text, setText] = useState('')
  const since = useRef(0)
  const bottom = useRef<HTMLDivElement>(null)

  const poll = useCallback(() => {
    api<CouncilState>('council?since=' + since.current).then((s) => {
      setState(s)
      if (s.messages.length) {
        setMsgs((old) => {
          const byId = new Map(old.map((m) => [m.id, m]))
          for (const m of s.messages) byId.set(m.id, m)
          const all = [...byId.values()].sort((a, b) => a.id - b.id)
          since.current = Math.max(since.current, ...all.filter((m) => m.done).map((m) => m.id))
          return all
        })
      }
    }).catch(onError)
  }, [onError])

  const active = !!state?.busy || msgs.some((m) => !m.done)
  useEffect(() => {
    poll()
    const id = setInterval(poll, active ? 900 : 4000)
    return () => clearInterval(id)
  }, [poll, active])
  useEffect(() => { bottom.current?.scrollIntoView({ block: 'end' }) }, [msgs.length, msgs[msgs.length - 1]?.text.length])

  const look = () => api('council/look', { method: 'POST', body: { ids, text } }).then(() => { setText(''); poll() }).catch(onError)
  const chat = () => api('council/chat', { method: 'POST', body: { text } }).then(() => { setText(''); poll() }).catch(onError)
  const tryIt = (p: Proposal) => api(`proposals/${p.id}/try`, { method: 'POST' }).then(() => { poll(); onBranched() }).catch(onError)
  const dismiss = (p: Proposal) => api(`proposals/${p.id}/dismiss`, { method: 'POST' }).then(poll).catch(onError)

  return (
    <div className="lab-guide">
      <div className="lab-roles">
        {state?.roles.map((r) => (
          <label key={r.role} className={'lab-role' + (r.available ? ' on' : '')} title={r.reason || r.model}>
            <i style={{ background: WHO_COLOR[r.role] }} />{r.label}
            <select className="lab-mini" value={models.find((m) => m.provider === r.provider && m.model === r.model)?.key ?? ''}
              onChange={(e) => api('council/select', { method: 'POST', body: { role: r.role, key: e.target.value } }).then(poll).catch(onError)}>
              <option value="">（なし）</option>
              {models.filter((m) => r.role !== 'vision' || m.images).map((m) => (
                <option key={m.key} value={m.key}>{m.label}{m.available ? '' : '（未設定）'}</option>
              ))}
            </select>
            {!r.available && r.reason && <span className="mono muted"> {r.reason}</span>}
          </label>
        ))}
        {state && <span className="mono muted lab-cost">今日 ${state.spent_today.toFixed(3)} / 上限 ${state.limit_usd.toFixed(2)}</span>}
      </div>
      {state?.bridge && (
        <p className="lab-note lab-bridge">中心の AI（API キー）が未設定なので、「見てもらう」は Claude Code に渡します。
          このリポジトリで Claude Code を開き <code>/guide</code> と打つと、同じパケットを読んで助言し、提案カードをここに出します。</p>
      )}

      <div className="lab-chat">
        {msgs.length === 0 && <p className="muted lab-note">「見てもらう」と、いま並んでいる宇宙の観測パケット（「AI に渡すもの」と同じ）を AI たちに渡します。
          見る係は画像と動き、別の視点は事件簿、中心はその全部を読んで、あなたと話します。</p>}
        {msgs.map((m) => (
          <div key={m.id} className={'lab-msg who-' + m.who}>
            <div className="lab-msg-head">
              <b style={{ color: WHO_COLOR[m.who] ?? 'var(--ink)' }}>{m.label}</b>
              {m.model && <span className="mono muted"> {m.model}</span>}
              {m.who === 'vision' && <span className="lab-unmeasured">見た目（未測定）</span>}
              <span className="mono muted"> {m.at}{m.done ? '' : ' …'}</span>
              {m.usage && <span className="mono muted"> · {m.usage.input_tokens}+{m.usage.output_tokens} tok{m.usd ? ` · $${m.usd.toFixed(4)}` : ''}</span>}
            </div>
            <div className="lab-msg-text">{m.text}</div>
          </div>
        ))}
        <div ref={bottom} />
      </div>

      {state && state.proposals.length > 0 && (
        <div className="lab-section">
          <div className="eyebrow">提案カード（押すまで何も起きない）</div>
          {state.proposals.map((p) => (
            <div key={p.id} className={'lab-card st-' + p.status}>
              <div><b>#{p.id}</b> <span className="mono">{p.parent_label} から分岐</span> <span className="muted">（{p.source === 'core' ? '中心' : p.source}）</span></div>
              <div className="mono lab-card-change">
                {Object.entries(p.set).map(([k, v]) => `${k}=${v}`).join(', ')}
                {p.perturb && ` 摂動 ${p.perturb.name} ${Object.entries(p.perturb.args).map(([k, v]) => `${k}=${v}`).join(' ')}`}
              </div>
              {p.put_in && <div><span className="aq-put">置くもの:</span> {p.put_in}</div>}
              {p.why && <div>なぜ: {p.why}</div>}
              {p.predict && <div>予想（測定）: {p.predict}</div>}
              {p.status === 'open' ? (
                <div className="lab-row">
                  <button className="tbtn pri" onClick={() => tryIt(p)}>分岐して試す</button>
                  <button className="tbtn" onClick={() => dismiss(p)}>見送る</button>
                </div>
              ) : <div className="muted">{p.status === 'tried' ? `試した → 新しい宇宙 ${p.child}` : '見送った'}</div>}
            </div>
          ))}
        </div>
      )}

      <div className="lab-compose">
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3}
          placeholder="あなたの考えや質問（例：F を少し上げたら分裂は速くなる？）" />
        <div className="lab-row">
          <button className="tbtn pri" disabled={active || !ids.length} onClick={look}>見てもらう（いまの宇宙 {ids.length} 個）</button>
          <button className="tbtn" disabled={active || !text.trim() || !msgs.length} onClick={chat}>話す</button>
        </div>
      </div>
    </div>
  )
}
