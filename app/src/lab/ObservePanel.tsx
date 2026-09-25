import { useEffect, useState } from 'react'
import { api } from './api'

// "AI に渡したもの": the observation packet exactly as every AI in the council receives it -- the
// mechanically detected 事件簿 (text), key frames each with its caption, and the motion sequence. A person can
// check here what the AIs were shown before trusting anything they say about it.

interface PacketImage { kind: string; t: number; step: number; caption: string; src: string }
interface PacketUniverse {
  id: string; label: string; title: string; images: PacketImage[]
  motion: { t: number[]; caption: string; frames: string[]; has_mp4: boolean }
}
export interface Packet { text: string; universes: PacketUniverse[]; saved: string | null }

function Motion({ m }: { m: PacketUniverse['motion'] }) {
  const [i, setI] = useState(0)
  useEffect(() => {
    if (m.frames.length < 2) return
    const id = setInterval(() => setI((x) => (x + 1) % m.frames.length), 350)
    return () => clearInterval(id)
  }, [m.frames.length])
  if (!m.frames.length) return null
  return (
    <figure className="lab-fig">
      <figcaption>{m.caption}（いま t={m.t[i]?.toFixed(1)}）{m.has_mp4 ? '・mp4 も渡す' : ''}</figcaption>
      <img src={m.frames[i]} alt={m.caption} />
    </figure>
  )
}

export default function ObservePanel({ ids, onError, onPacket }: {
  ids: string[]; onError: (e: unknown) => void; onPacket?: (p: Packet) => void
}) {
  const [packet, setPacket] = useState<Packet | null>(null)
  const [busy, setBusy] = useState(false)
  const run = () => {
    setBusy(true)
    api<Packet>('observe', { method: 'POST', body: { ids } })
      .then((p) => { setPacket(p); onPacket?.(p) }).catch(onError).finally(() => setBusy(false))
  }
  return (
    <div>
      <div className="lab-row">
        <button className="tbtn pri" disabled={busy || !ids.length} onClick={run}>{busy ? 'まとめています…' : 'いまの様子をまとめる'}</button>
      </div>
      <p className="muted lab-note">どの AI にも、ここに出るものと同じものを渡します（測定から機械的に作った事件簿・説明つきの画像・動き）。解釈は入っていません。</p>
      {packet && (
        <>
          {packet.saved && <div className="mono muted lab-note">保存: {packet.saved}</div>}
          <details className="lab-section" open>
            <summary>事件簿（文章しか読めない AI はこれだけで「見る」）</summary>
            <pre className="lab-pre">{packet.text}</pre>
          </details>
          {packet.universes.map((u) => (
            <details key={u.id} className="lab-section">
              <summary>宇宙 {u.label} の画像 {u.images.length} 枚・動き {u.motion.frames.length} コマ</summary>
              {u.images.map((im, i) => (
                <figure key={i} className="lab-fig">
                  <figcaption>{im.caption}</figcaption>
                  <img src={im.src} alt={im.caption} />
                </figure>
              ))}
              <Motion m={u.motion} />
            </details>
          ))}
        </>
      )}
    </div>
  )
}
