import { useCallback, useEffect, useRef, useState } from 'react'
import { speechChunks } from './speechText'

interface RecognitionResult { readonly isFinal: boolean; readonly length: number; readonly [index: number]: { transcript: string } }
interface RecognitionEvent { readonly resultIndex: number; readonly results: { readonly length: number; readonly [index: number]: RecognitionResult } }
interface Recognition {
  lang: string; continuous: boolean; interimResults: boolean; maxAlternatives: number
  onstart: (() => void) | null; onend: (() => void) | null
  onresult: ((event: RecognitionEvent) => void) | null
  onerror: ((event: { error: string }) => void) | null
  start(): void; stop(): void; abort(): void
}
type RecognitionConstructor = new () => Recognition
type VoiceWindow = Window & { SpeechRecognition?: RecognitionConstructor; webkitSpeechRecognition?: RecognitionConstructor }
export interface SpeechMessage { id: number; who: string; text: string; done: boolean }
type InputPhase = 'idle' | 'starting' | 'listening' | 'stopping'
interface Settings { auto: boolean; rate: number; voice: string }
const SETTINGS = 'aeterna-speech-settings-v1'
function initialSettings(): Settings {
  try {
    const stored = JSON.parse(localStorage.getItem(SETTINGS) || '{}')
    return { auto: stored.auto === true, rate: typeof stored.rate === 'number' && stored.rate >= 0.7 && stored.rate <= 1.4 ? stored.rate : 1, voice: typeof stored.voice === 'string' ? stored.voice : '' }
  } catch { return { auto: false, rate: 1, voice: '' } }
}
function detach(recognition: Recognition) {
  recognition.onstart = recognition.onend = recognition.onresult = recognition.onerror = null
  try { recognition.abort() } catch { /* Already ended. */ }
}
function inputError(code: string): string {
  if (code === 'not-allowed' || code === 'service-not-allowed') return 'マイクを使えませんでした。ブラウザのマイク許可を確認して、もう一度お試しください。'
  if (code === 'audio-capture') return 'マイクが見つからないか、別のアプリが使用しています。接続を確認してください。'
  if (code === 'network') return '音声認識サービスに接続できませんでした。通信状態を確認するか、文字で入力してください。'
  if (code === 'no-speech') return '音声を聞き取れませんでした。もう一度マイクを押して話してください。'
  if (code === 'language-not-supported') return 'このブラウザでは日本語の音声認識を利用できません。文字やキーボードの音声入力をお使いください。'
  return '音声入力を続けられませんでした。もう一度試すか、文字で入力してください。'
}

/** Browser speech only; no audio file, voice API key, simulator command or automatic send. */
export default function useSpeech({ enabled, messages, hydrated, onTranscript }: {
  enabled: boolean; messages: SpeechMessage[]; hydrated: boolean; onTranscript: (text: string) => void
}) {
  const [settings, setSettings] = useState(initialSettings)
  const [phase, setPhase] = useState<InputPhase>('idle')
  const [interim, setInterim] = useState('')
  const [inputFailure, setInputFailure] = useState('')
  const [outputFailure, setOutputFailure] = useState('')
  const [outputPhase, setOutputPhase] = useState<'idle' | 'starting' | 'speaking'>('idle')
  const outputTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const inputStopping = useRef(false)
  const [speakingId, setSpeakingId] = useState<number | null>(null)
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])
  const recognition = useRef<Recognition | null>(null)
  const stoppingTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const generation = useRef(0)
  const ownedUtterance = useRef<SpeechSynthesisUtterance | null>(null)
  const onFinal = useRef(onTranscript); onFinal.current = onTranscript
  const allowed = useRef(enabled); allowed.current = enabled
  const seenReplies = useRef(new Set<number>())
  const baselineReady = useRef(false)
  const pendingReply = useRef<SpeechMessage | null>(null)
  const ctor = typeof window === 'undefined' ? undefined : (window as VoiceWindow).SpeechRecognition || (window as VoiceWindow).webkitSpeechRecognition
  const secure = typeof window !== 'undefined' && window.isSecureContext
  const canListen = !!ctor && secure
  const canSpeak = typeof window !== 'undefined' && !!window.speechSynthesis && typeof window.SpeechSynthesisUtterance === 'function'

  const clearTimer = useCallback(() => {
    if (stoppingTimer.current) clearTimeout(stoppingTimer.current)
    stoppingTimer.current = null
  }, [])
  const cancelInput = useCallback(() => {
    clearTimer()
    const current = recognition.current; recognition.current = null
    if (current) detach(current)
    setPhase('idle'); setInterim('')
  }, [clearTimer])
  const stopSpeaking = useCallback(() => {
    generation.current++
    if (outputTimer.current) clearTimeout(outputTimer.current)
    outputTimer.current = null
    if (ownedUtterance.current) {
      ownedUtterance.current = null
      try { window.speechSynthesis.cancel() } catch { /* Engine may have closed. */ }
    }
    setSpeakingId(null); setOutputPhase('idle')
  }, [])

  useEffect(() => {
    try { localStorage.setItem(SETTINGS, JSON.stringify(settings)) } catch { /* Private browsing remains usable. */ }
  }, [settings])
  useEffect(() => {
    if (!canSpeak) return
    const synth = window.speechSynthesis
    const update = () => { try { setVoices(synth.getVoices()) } catch { setVoices([]) } }
    update(); synth.addEventListener('voiceschanged', update)
    return () => synth.removeEventListener('voiceschanged', update)
  }, [canSpeak])

  const read = useCallback((text: string, id: number) => {
    if (!allowed.current || document.visibilityState === 'hidden') return
    if (recognition.current) { setOutputFailure('音声入力を止めてから読み上げをお使いください。'); return }
    if (!canSpeak) { setOutputFailure('このブラウザは返答の読み上げに対応していません。'); return }
    stopSpeaking(); setOutputFailure('')
    const chunks = speechChunks(text)
    if (!chunks.length) return
    const synth = window.speechSynthesis
    const token = generation.current
    let available: SpeechSynthesisVoice[] = []
    try { available = synth.getVoices() } catch { /* Let the engine choose its default voice. */ }
    const voice = available.find(v => v.voiceURI === settings.voice)
      ?? available.find(v => /^ja\b/i.test(v.lang) && v.localService)
      ?? available.find(v => /^ja\b/i.test(v.lang))
    setSpeakingId(id)
    const speakChunk = (index: number) => {
      if (token !== generation.current || !allowed.current) return
      if (index >= chunks.length) { ownedUtterance.current = null; setSpeakingId(null); setOutputPhase('idle'); return }
      const utterance = new SpeechSynthesisUtterance(chunks[index])
      utterance.lang = voice?.lang || 'ja-JP'; utterance.rate = settings.rate
      if (voice) utterance.voice = voice
      ownedUtterance.current = utterance; setOutputPhase('starting')
      utterance.onstart = () => {
        if (token !== generation.current) return
        if (outputTimer.current) clearTimeout(outputTimer.current)
        outputTimer.current = null; setOutputPhase('speaking')
      }
      utterance.onend = () => {
        if (token !== generation.current) return
        if (outputTimer.current) clearTimeout(outputTimer.current)
        outputTimer.current = null; speakChunk(index + 1)
      }
      utterance.onerror = (event) => {
        if (token !== generation.current) return
        generation.current++
        if (outputTimer.current) clearTimeout(outputTimer.current)
        outputTimer.current = null; ownedUtterance.current = null; setSpeakingId(null); setOutputPhase('idle')
        if (event.error === 'canceled' || event.error === 'interrupted') return
        setOutputFailure(event.error === 'not-allowed'
          ? '自動読み上げをこのブラウザが制限しています。返答の「読み上げ」を押すと再試行できます。'
          : '読み上げを開始できませんでした。端末の音声設定を確認し、返答の「読み上げ」で再試行してください。')
      }
      try {
        // Some browsers silently refuse autoplay; never report playback before onstart.
        outputTimer.current = setTimeout(() => {
          if (token === generation.current && ownedUtterance.current === utterance) {
            stopSpeaking(); setOutputFailure('音声の再生が始まりませんでした。返答の「読み上げ」を押して再試行してください。')
          }
        }, 5000)
        synth.resume(); synth.speak(utterance)
      } catch {
        stopSpeaking(); setOutputFailure('読み上げを開始できませんでした。返答の「読み上げ」で再試行してください。')
      }
    }
    speakChunk(0)
  }, [canSpeak, settings.rate, settings.voice, stopSpeaking])

  const stopInput = useCallback(() => {
    const current = recognition.current
    if (!current) return
    inputStopping.current = true; setPhase('stopping')
    try {
      current.stop()
      // A faulty engine must not leave a microphone indicator stuck forever.
      clearTimer()
      stoppingTimer.current = setTimeout(() => {
        if (recognition.current === current) {
          cancelInput(); setInputFailure('音声入力を終了しました。確定した文字を確認してください。')
        }
      }, 5000)
    } catch { cancelInput() }
  }, [cancelInput, clearTimer])

  const toggleInput = useCallback(() => {
    if (recognition.current) { stopInput(); return }
    if (!canListen || !ctor || !allowed.current) return
    stopSpeaking(); setInputFailure(''); setInterim('')
    const current = new ctor()
    const committed = new Set<number>()
    recognition.current = current; inputStopping.current = false; setPhase('starting')
    current.lang = 'ja-JP'; current.continuous = true; current.interimResults = true; current.maxAlternatives = 1
    current.onstart = () => {
      if (recognition.current !== current) return
      if (inputStopping.current) { try { current.stop() } catch { cancelInput() } }
      else setPhase('listening')
    }
    current.onresult = event => {
      if (recognition.current !== current || !allowed.current) return
      const partial: string[] = []
      for (let index = 0; index < event.results.length; index++) {
        const result = event.results[index]
        const transcript = result[0]?.transcript?.trim() || ''
        if (result.isFinal && !committed.has(index) && index >= event.resultIndex) {
          committed.add(index)
          if (transcript) onFinal.current(transcript)
        } else if (!result.isFinal && transcript) partial.push(transcript)
      }
      setInterim(partial.join(' '))
    }
    current.onerror = event => {
      if (recognition.current !== current) return
      if (event.error !== 'aborted') setInputFailure(inputError(event.error))
      cancelInput()
    }
    current.onend = () => { if (recognition.current === current) cancelInput() }
    try { current.start() } catch { cancelInput(); setInputFailure('マイクを開始できませんでした。ブラウザの許可と端末の設定を確認してください。') }
  }, [canListen, ctor, stopSpeaking, stopInput, cancelInput])

  useEffect(() => {
    if (!hydrated) return
    const replies = messages.filter(m => m.done && m.text.trim() && (m.who === 'core' || m.who === 'claude-code'))
    if (!enabled) { baselineReady.current = false; pendingReply.current = null; return }
    if (!baselineReady.current) {
      replies.forEach(m => seenReplies.current.add(m.id)); baselineReady.current = true; return
    }
    const fresh = replies.filter(m => !seenReplies.current.has(m.id))
    replies.forEach(m => seenReplies.current.add(m.id))
    if (!settings.auto || document.visibilityState === 'hidden') { pendingReply.current = null; return }
    if (fresh.length) pendingReply.current = fresh[fresh.length - 1]
    if (pendingReply.current && !recognition.current) {
      const reply = pendingReply.current; pendingReply.current = null; read(reply.text, reply.id)
    }
  }, [messages, hydrated, enabled, settings.auto, phase, read])

  useEffect(() => {
    if (!enabled) { cancelInput(); stopSpeaking(); pendingReply.current = null }
  }, [enabled, cancelInput, stopSpeaking])
  useEffect(() => {
    const hide = () => {
      if (document.visibilityState === 'hidden') {
        cancelInput(); stopSpeaking(); pendingReply.current = null
      }
    }
    const pageHide = () => { cancelInput(); stopSpeaking() }
    document.addEventListener('visibilitychange', hide); window.addEventListener('pagehide', pageHide)
    return () => {
      document.removeEventListener('visibilitychange', hide); window.removeEventListener('pagehide', pageHide)
      clearTimer()
      const current = recognition.current; recognition.current = null
      if (current) detach(current)
      generation.current++
      if (outputTimer.current) clearTimeout(outputTimer.current)
      outputTimer.current = null
      if (ownedUtterance.current) { ownedUtterance.current = null; try { window.speechSynthesis.cancel() } catch { /* Closed. */ } }
    }
  }, [cancelInput, stopSpeaking, clearTimer])

  return {
    phase, interim, inputFailure, outputFailure, canListen, canSpeak, secure, speakingId, outputPhase, voices, settings,
    toggleInput, stopInput, stopSpeaking, read,
    setAuto: (auto: boolean) => { setSettings(s => ({ ...s, auto })); if (!auto) { pendingReply.current = null; stopSpeaking() } },
    setRate: (rate: number) => setSettings(s => ({ ...s, rate })),
    setVoice: (voice: string) => setSettings(s => ({ ...s, voice })),
  }
}
