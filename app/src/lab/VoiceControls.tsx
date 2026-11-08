import type useSpeech from './useSpeech'
type Voice = ReturnType<typeof useSpeech>
export function MicIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><rect x="9" y="2.5" width="6" height="12" rx="3"/><path d="M5.5 10.5v1a6.5 6.5 0 0 0 13 0v-1M12 18v3.5M8.5 21.5h7"/></svg>
}
export function SpeakerIcon() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="m11 4-6 5H2v6h3l6 5V4ZM15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14"/></svg>
}
export default function VoiceControls({ voice }: { voice: Voice }) {
  const busy = voice.phase !== 'idle'
  return <div className="lab-voice">
    <div className="lab-voice-row">
      <button className={'tbtn lab-mic' + (busy ? ' listening' : '')} type="button" disabled={!voice.canListen || voice.phase === 'stopping'} aria-pressed={busy} onClick={voice.toggleInput}>
        <MicIcon/>{voice.phase === 'starting' ? 'マイクを準備中…' : voice.phase === 'stopping' ? '聞き取りを確定中…' : busy ? '入力を止める' : '声で入力'}
      </button>
      <label className="lab-auto-speech"><input type="checkbox" checked={voice.settings.auto} disabled={!voice.canSpeak} onChange={e=>voice.setAuto(e.target.checked)}/>返答を自動で読み上げる</label>
    </div>
    {busy && <div className="lab-voice-preview"><span role="status"><i/>{voice.phase === 'stopping' ? '確定した文字を反映しています' : voice.phase === 'starting' ? 'ブラウザのマイク許可を確認しています' : '聞き取り中 · まだ送信されません'}</span>
      {voice.interim && <output aria-live="off">{voice.interim}<small>（未確定）</small></output>}
    </div>}
    {voice.speakingId !== null && <div className="lab-voice-speaking" role="status"><SpeakerIcon/>{voice.outputPhase === 'speaking' ? '返答を読み上げています' : '読み上げを準備しています'}<button type="button" className="tbtn" onClick={voice.stopSpeaking}>読み上げ停止</button></div>}
    {voice.inputFailure && <p className="lab-voice-error" role="status">{voice.inputFailure}</p>}
    {voice.outputFailure && <p className="lab-voice-error" role="status">{voice.outputFailure}</p>}
    {!voice.canListen && <p className="lab-voice-note">{!voice.secure ? '音声入力はHTTPSまたはlocalhostで開いた画面で使えます。' : 'このブラウザはマイクによる音声入力に対応していません。'}文字入力や、端末のキーボードのマイク入力も使えます。</p>}
    {!voice.canSpeak && <p className="lab-voice-note">このブラウザは返答の読み上げに対応していません。返答は文字で確認できます。</p>}
    <p className="lab-voice-note">音声と読み上げ文は、設定によってブラウザの音声サービス提供元へ送信される場合があります。</p>
    <details className="lab-fold lab-voice-options"><summary>音声の設定・使い方</summary>
      <label>読み上げ速度 <output>{voice.settings.rate.toFixed(1)}倍</output><input aria-label="読み上げ速度" type="range" min={0.7} max={1.4} step={0.1} value={voice.settings.rate} disabled={!voice.canSpeak} onChange={e=>voice.setRate(Number(e.target.value))}/></label>
      <label>読み上げる声<select aria-label="読み上げる声" value={voice.settings.voice} disabled={!voice.canSpeak} onChange={e=>voice.setVoice(e.target.value)}><option value="">自動（日本語を優先）</option>{voice.voices.map(v=><option key={v.voiceURI} value={v.voiceURI}>{v.name} · {v.lang}{v.localService ? ' · 端末内' : ''}</option>)}</select></label>
      <p>声と速度は次の読み上げから反映します。自動読み上げは新しく届いた完成済みの返答だけが対象です。各返答の「読み上げ」でも聞けます。</p>
      <p>マイクを止め、文字を確認・修正してから送信してください。音声入力中は読み上げを止めます。タブやパネルを閉じると、音声入力・読み上げも終了します。</p>
      <p>音声や読み上げる文章はブラウザ・端末の音声サービスが処理し、設定によって提供元へ送信される場合があります。このアプリは音声ファイルを保存しません。</p>
    </details>
  </div>
}
