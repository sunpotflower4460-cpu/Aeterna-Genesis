import { useEffect, useMemo, useState } from 'react'
import { useStore } from '../store'
import type { Aquarium, AquariumDraft, AquariumIntentMode, AquariumNote } from '../lib/types'

const DRAFT_KEY = 'aeterna-aquarium-drafts-v1'

const originLabel = { human: 'Human', ai: 'AI', joint: 'Human × AI' } as const
const originMark = { human: '○', ai: '✦', joint: '◇' } as const

function badge(text: string) {
  return (
    <span className="mono" style={{
      fontSize: 10.5, padding: '4px 7px', borderRadius: 999,
      border: '1px solid var(--line)', color: 'var(--muted)', background: 'rgba(255,255,255,.025)',
    }}>{text}</span>
  )
}

function readable(value: unknown): string {
  if (Array.isArray(value)) return value.join(' · ')
  if (value && typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function AquariumCard({ aquarium, selected, onClick }: { aquarium: Aquarium; selected: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{
      width: '100%', textAlign: 'left', padding: 14, borderRadius: 14,
      border: selected ? '1px solid rgba(79,227,224,.52)' : '1px solid var(--line)',
      background: selected ? 'rgba(79,227,224,.07)' : 'var(--panel)', color: 'var(--ink)',
      display: 'grid', gap: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <div className="mono" style={{ color: 'var(--accent)', fontSize: 10.5 }}>{aquarium.aquarium_id}</div>
        <div className="mono muted" style={{ fontSize: 10.5 }}>{originMark[aquarium.origin]} {originLabel[aquarium.origin]}</div>
      </div>
      <div style={{ fontSize: 14.5, fontWeight: 650 }}>{aquarium.title}</div>
      <div className="muted" style={{ fontSize: 12, lineHeight: 1.55 }}>{aquarium.summary}</div>
      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
        {badge(aquarium.intent.mode === 'open_ended' ? 'OPEN-ENDED' : 'GOAL-DIRECTED')}
        {badge(aquarium.status.toUpperCase())}
      </div>
    </button>
  )
}

function NoteRow({ note }: { note: AquariumNote }) {
  const label = note.author_role === 'ai' ? 'AI Direction' : note.author_role === 'human' ? 'Human Note' : 'Joint Note'
  return (
    <div style={{ padding: '12px 0', borderBottom: '1px solid var(--line)' }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6, flexWrap: 'wrap' }}>
        <span className="mono" style={{ color: note.author_role === 'ai' ? 'var(--accent)' : 'var(--ink)', fontSize: 10.5 }}>
          {originMark[note.author_role]} {label}
        </span>
        <span className="mono muted" style={{ fontSize: 10 }}>{note.kind}</span>
        {note.status && <span className="mono muted" style={{ fontSize: 10 }}>{note.status}</span>}
      </div>
      <div style={{ fontSize: 13, lineHeight: 1.7 }}>{note.text}</div>
      {note.evidence_refs.length > 0 && (
        <div className="mono muted" style={{ fontSize: 9.5, marginTop: 7, lineHeight: 1.5 }}>
          refs: {note.evidence_refs.join(' · ')}
        </div>
      )}
    </div>
  )
}

function DraftComposer() {
  const [title, setTitle] = useState('')
  const [goal, setGoal] = useState('')
  const [note, setNote] = useState('')
  const [intentMode, setIntentMode] = useState<AquariumIntentMode>('goal_directed')
  const [drafts, setDrafts] = useState<AquariumDraft[]>([])

  useEffect(() => {
    try {
      const saved = localStorage.getItem(DRAFT_KEY)
      if (saved) setDrafts(JSON.parse(saved))
    } catch {
      // Local-only convenience. Failure must never affect the Observatory or science state.
    }
  }, [])

  const save = () => {
    if (!title.trim() || !goal.trim()) return
    const next = [{ title: title.trim(), goal: goal.trim(), note: note.trim(), intentMode, createdAt: new Date().toISOString() }, ...drafts]
    setDrafts(next)
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify(next)) } catch { /* local draft only */ }
    setTitle('')
    setGoal('')
    setNote('')
  }

  return (
    <section className="glass" style={{ padding: 18, border: '1px solid var(--line)', marginTop: 18 }}>
      <p className="eyebrow" style={{ margin: 0 }}>Your idea</p>
      <h3 style={{ margin: '6px 0 4px', fontSize: 17 }}>新しい宇宙水槽を考える</h3>
      <p className="muted" style={{ margin: '0 0 14px', fontSize: 12.5, lineHeight: 1.6 }}>
        ここではアイディアだけを保存します。物理はまだ実行しません。AI Runner接続後も、目的文はplanningだけが読み、solverは読みません。
      </p>
      <div style={{ display: 'grid', gap: 10 }}>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="水槽の名前 例：光を食べる関係網" style={inputStyle} />
        <select value={intentMode} onChange={(e) => setIntentMode(e.target.value as AquariumIntentMode)} style={inputStyle}>
          <option value="goal_directed">目的を見据える水槽</option>
          <option value="open_ended">何が起こるか決めない水槽</option>
        </select>
        <textarea value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="何を見たい？ どんな世界を試したい？" rows={3} style={{ ...inputStyle, resize: 'vertical' }} />
        <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="入れてみたい前提条件や思いつき（任意）" rows={2} style={{ ...inputStyle, resize: 'vertical' }} />
        <button className="lens" onClick={save} disabled={!title.trim() || !goal.trim()} style={{ justifySelf: 'start' }}>
          ＋ アイディアを下書き保存
        </button>
      </div>
      {drafts.length > 0 && (
        <div style={{ marginTop: 16, display: 'grid', gap: 8 }}>
          <div className="mono muted" style={{ fontSize: 10.5 }}>LOCAL DRAFTS · {drafts.length}</div>
          {drafts.slice(0, 4).map((d, i) => (
            <div key={d.createdAt + i} style={{ padding: 10, borderRadius: 10, border: '1px solid var(--line)', background: 'rgba(255,255,255,.02)' }}>
              <div style={{ fontWeight: 600, fontSize: 12.5 }}>{d.title}</div>
              <div className="muted" style={{ fontSize: 11.5, marginTop: 4, lineHeight: 1.5 }}>{d.goal}</div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

const inputStyle = {
  width: '100%', boxSizing: 'border-box' as const, borderRadius: 9, padding: '10px 11px',
  border: '1px solid var(--line)', background: 'rgba(4,7,14,.72)', color: 'var(--ink)', font: 'inherit',
}

export default function AquariumLab() {
  const registry = useStore((s) => s.aquariumRegistry)
  const notebook = useStore((s) => s.aquariumNotebook)
  const toLobby = useStore((s) => s.toLobby)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const aquaria = registry?.aquaria || []
  const selected = aquaria.find((a) => a.aquarium_id === selectedId) || aquaria[0] || null
  const notes = useMemo(() => {
    if (!selected || !notebook) return []
    return notebook.entries.filter((n) => n.aquarium_id === selected.aquarium_id)
  }, [notebook, selected])

  const active = aquaria.filter((a) => a.status === 'active').length
  const humanBorn = aquaria.filter((a) => a.origin === 'human').length
  const aiBorn = aquaria.filter((a) => a.origin === 'ai').length

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '24px 20px 80px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <p className="eyebrow" style={{ margin: '0 0 7px' }}>Aeterna · Universe Aquarium Lab</p>
            <h1 style={{ margin: 0, fontSize: 29, fontWeight: 650, letterSpacing: '-.025em' }}>宇宙水槽</h1>
            <p className="muted" style={{ margin: '7px 0 0', maxWidth: 690, lineHeight: 1.6, fontSize: 13 }}>
              人間とAIが「こんな世界を見たい」を共有し、結果を置かずに前提条件を探す研究室。
            </p>
          </div>
          <button className="lens" onClick={toLobby}>← Observatory</button>
        </div>

        <div className="glass" style={{ marginTop: 18, padding: '14px 16px', border: '1px solid rgba(79,227,224,.24)' }}>
          <div style={{ fontWeight: 620, fontSize: 13.5 }}>意図は自由。結果は仕込まない。</div>
          <div className="muted" style={{ fontSize: 12, marginTop: 4, lineHeight: 1.6 }}>
            Goal-directedでもOpen-endedでも研究できる。Intentは次のRecipeを考えるために使えるが、物理solverはIntent文を読まない。
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 14 }}>
          {badge(`${aquaria.length} AQUARIA`)}
          {badge(`${active} ACTIVE`)}
          {badge(`${humanBorn} HUMAN IDEAS`)}
          {badge(`${aiBorn} AI IDEAS`)}
        </div>

        {!registry ? (
          <div className="muted" style={{ padding: '42px 0' }}>Aquarium registry がまだ app data にありません。</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(240px, 330px) minmax(0, 1fr)', gap: 18, marginTop: 18, alignItems: 'start' }}>
            <div style={{ display: 'grid', gap: 9 }}>
              {aquaria.map((a) => (
                <AquariumCard key={a.aquarium_id} aquarium={a} selected={selected?.aquarium_id === a.aquarium_id} onClick={() => setSelectedId(a.aquarium_id)} />
              ))}
            </div>

            {selected && (
              <div style={{ display: 'grid', gap: 14 }}>
                <section className="glass" style={{ padding: 18, border: '1px solid var(--line)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 14, flexWrap: 'wrap' }}>
                    <div>
                      <div className="mono" style={{ color: 'var(--accent)', fontSize: 10.5 }}>{selected.aquarium_id}</div>
                      <h2 style={{ margin: '5px 0 5px', fontSize: 22 }}>{selected.title}</h2>
                      <div className="muted" style={{ fontSize: 12.5, lineHeight: 1.6, maxWidth: 720 }}>{selected.summary}</div>
                    </div>
                    <div style={{ display: 'flex', gap: 5, alignItems: 'start', flexWrap: 'wrap' }}>
                      {badge(originLabel[selected.origin])}{badge(selected.status.toUpperCase())}
                    </div>
                  </div>

                  <div style={{ marginTop: 18, padding: 14, borderRadius: 12, background: 'rgba(79,227,224,.055)', border: '1px solid rgba(79,227,224,.16)' }}>
                    <div className="mono" style={{ fontSize: 10, color: 'var(--accent)' }}>INTENT · {selected.intent.mode}</div>
                    <div style={{ marginTop: 7, fontSize: 14, lineHeight: 1.7 }}>{selected.intent.goal}</div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(210px,1fr))', gap: 14, marginTop: 16 }}>
                    <div>
                      <div className="mono muted" style={{ fontSize: 10, marginBottom: 8 }}>AQUARIUM CLASSES</div>
                      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>{selected.classes.map((c) => <span key={c}>{badge(c)}</span>)}</div>
                    </div>
                    <div>
                      <div className="mono muted" style={{ fontSize: 10, marginBottom: 8 }}>OBSERVE</div>
                      <div className="muted" style={{ fontSize: 12, lineHeight: 1.65 }}>{selected.observation_focus.join(' · ')}</div>
                    </div>
                  </div>

                  <div style={{ marginTop: 18 }}>
                    <div className="mono muted" style={{ fontSize: 10, marginBottom: 8 }}>RECIPE SPACE · WHAT MAY BE CHANGED</div>
                    <div style={{ display: 'grid', gap: 6 }}>
                      {Object.entries(selected.recipe_space).map(([k, v]) => (
                        <div key={k} style={{ display: 'grid', gridTemplateColumns: 'minmax(120px, .35fr) 1fr', gap: 10, padding: '7px 0', borderBottom: '1px solid var(--line)' }}>
                          <div className="mono" style={{ color: 'var(--faint)', fontSize: 10.5 }}>{k}</div>
                          <div className="muted" style={{ fontSize: 11.5, lineHeight: 1.55 }}>{readable(v)}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={{ marginTop: 14, display: 'flex', gap: 7, flexWrap: 'wrap' }}>
                    {badge('planning ≠ evidence')}{badge('intent hidden from solver')}{badge('no auto promotion')}
                  </div>
                </section>

                <section className="glass" style={{ padding: 18, border: '1px solid var(--line)' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10 }}>
                    <div>
                      <p className="eyebrow" style={{ margin: 0 }}>Shared notebook</p>
                      <h3 style={{ margin: '5px 0 0', fontSize: 17 }}>人間のメモ × AIの方向書</h3>
                    </div>
                    <span className="mono muted" style={{ fontSize: 10 }}>{notes.length} notes</span>
                  </div>
                  <div style={{ marginTop: 8 }}>
                    {notes.length ? notes.map((n) => <NoteRow key={n.note_id} note={n} />) : (
                      <div className="muted" style={{ fontSize: 12, padding: '16px 0' }}>まだメモはありません。</div>
                    )}
                  </div>
                </section>
              </div>
            )}
          </div>
        )}

        <DraftComposer />
      </div>
    </div>
  )
}
