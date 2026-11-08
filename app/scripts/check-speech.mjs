// Browser speech API event-contract checks, not real microphone/audio-device verification.
// Uses a fresh isolated lab and a real 3D field. Never calls an external AI or recognition service.
import {chromium} from 'playwright'
import assert from 'node:assert/strict'
import {mkdir} from 'node:fs/promises'
import {createHash} from 'node:crypto'
const base=process.env.LAB_TEST_URL||'http://127.0.0.1:18772'
const artifacts=process.env.LAB_SCREENSHOT_DIR||'/tmp/aeterna-speech-check'
await mkdir(artifacts,{recursive:true})
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader']})
const page=await browser.newPage({viewport:{width:1400,height:1000},deviceScaleFactor:1})
const errors=[];page.on('pageerror',e=>errors.push(e.message))
const api=async(path,data)=>{
 const r=await page.request[data===undefined?'get':'post'](base+'/api/'+path,data===undefined?{}:{data})
 assert.ok(r.ok(),await r.text());return r.json()
}
async function frameHash(id){
 const r=await fetch(base+'/api/stream?u='+encodeURIComponent(id+':density'))
 const reader=r.body.getReader(),decoder=new TextDecoder();let text=''
 try{for(;;){const {done,value}=await reader.read();if(done)throw Error('Missing frame');text+=decoder.decode(value,{stream:true});let end
  while((end=text.indexOf('\n\n'))>=0){const event=text.slice(0,end);text=text.slice(end+2)
   if(event.startsWith('event: frame')){const frame=JSON.parse(event.split('\n').find(l=>l.startsWith('data:')).slice(5));if(frame.b64)return createHash('sha256').update(Buffer.from(frame.b64,'base64')).digest('hex')}
  }
 }}finally{await reader.cancel()}
}
function fakeSpeech(){
 const state={spoken:[],cancels:0,aborts:0,stops:0,currentInput:null,currentOutput:null,cancelled:null}
 class Recognition {
  start(){state.currentInput=this;queueMicrotask(()=>this.onstart?.())}
  stop(){state.stops++}
  abort(){state.aborts++;this.onend?.()}
 }
 class Utterance {constructor(text){this.text=text}}
 const synth=Object.assign(new EventTarget(),{
  getVoices:()=>[{voiceURI:'test-ja',name:'日本語（検証用）',lang:'ja-JP',localService:true,default:true}],
  resume(){},speak(utterance){state.spoken.push({text:utterance.text,rate:utterance.rate,lang:utterance.lang});state.currentOutput=utterance;queueMicrotask(()=>utterance.onstart?.())},
  cancel(){state.cancels++;state.cancelled=state.currentOutput;state.currentOutput=null},
 })
 Object.defineProperty(window,'SpeechRecognition',{value:Recognition,configurable:true})
 Object.defineProperty(window,'webkitSpeechRecognition',{value:undefined,configurable:true})
 Object.defineProperty(window,'SpeechSynthesisUtterance',{value:Utterance,configurable:true})
 Object.defineProperty(window,'speechSynthesis',{value:synth,configurable:true})
 window.__speech=Object.assign(state,{
  result(text,final=false){const result=Object.assign([{transcript:text}],{isFinal:final});state.currentInput?.onresult?.({resultIndex:0,results:[result]})},
  end(){state.currentInput?.onend?.()},deny(){state.currentInput?.onerror?.({error:'not-allowed'})},
  finishOutput(){state.currentOutput?.onend?.()},lateOutputEnd(){state.cancelled?.onend?.()},
  failOutput(){state.currentOutput?.onerror?.({error:'not-allowed'})},
 })
}
await page.addInitScript(fakeSpeech)
try{
 assert.equal((await api('council')).bridge,true,'Use an isolated lab without paid AI credentials')
 assert.equal((await api('universes')).universes.length,0,'Use a fresh lab server')
 const u=await api('universes',{white:'tdgl-3d',seed:2,play:false})
 await api(`universes/${u.id}/control`,{action:'step',n:100})
 const before={info:await api('universes/'+u.id),frame:await frameHash(u.id)}
 const history='動作確認用の過去の返答です。'+'これは読み上げの取消を確かめる検証用の文章です。'.repeat(8)
 await api('council/external',{who:'claude-code',text:history})
 await page.goto(base+'/#lab');await page.locator('.lab-read-reply').first().waitFor()
 assert.equal(await page.evaluate(()=>window.__speech.spoken.length),0,'History must never autoplay')
 await page.locator('.lab-read-reply').first().click()
 await page.getByText('返答を読み上げています',{exact:false}).waitFor()
 assert.equal(await page.evaluate(()=>window.__speech.spoken.length),1)
 const input=page.getByLabel('気になったことを質問する',{exact:true})
 await input.fill('既存の質問。')
 await page.getByRole('button',{name:'声で入力',exact:true}).click()
 await page.getByRole('button',{name:'入力を止める',exact:true}).waitFor()
 const spoken=await page.evaluate(()=>window.__speech.spoken.length)
 await page.evaluate(()=>window.__speech.lateOutputEnd())
 assert.equal(await page.evaluate(()=>window.__speech.spoken.length),spoken,'Cancelled audio must not restart a queued chunk')
 assert.ok(await page.evaluate(()=>window.__speech.cancels)>0)
 await page.evaluate(()=>window.__speech.result('ゆらぎを小さくしたら',false))
 await page.locator('.lab-voice-preview output').filter({hasText:'ゆらぎを小さくしたら'}).waitFor()
 assert.equal(await input.inputValue(),'既存の質問。','Interim speech must not overwrite the draft')
 await input.fill('編集した質問。')
 await page.getByRole('button',{name:'入力を止める',exact:true}).click()
 assert.ok(await page.getByRole('button',{name:'観測を保存してAIに渡す ↗',exact:true}).isDisabled())
 await page.evaluate(()=>{window.__speech.result('ゆらぎを0.002にしたらどうなる？',true);window.__speech.result('ゆらぎを0.002にしたらどうなる？',true);window.__speech.end()})
 await page.getByRole('button',{name:'声で入力',exact:true}).waitFor()
 assert.equal(await input.inputValue(),'編集した質問。 ゆらぎを0.002にしたらどうなる？')
 await page.getByRole('button',{name:'観測を保存してAIに渡す ↗',exact:true}).click()
 await page.getByText(/中心の AI（API）が使えないので/).waitFor()
 const conversation=await api('council')
 assert.ok(conversation.messages.some(m=>m.who==='you'&&m.text.includes('編集した質問。 ゆらぎを0.002にしたらどうなる？')))
 await page.getByRole('checkbox',{name:'返答を自動で読み上げる',exact:true}).check()
 await api('council/external',{who:'claude-code',text:'動作確認用の新しい返答です。予想は未検証で、結果は画面の測定値で確認します。'})
 await page.waitForFunction(()=>window.__speech.spoken.some(s=>s.text.includes('新しい返答')))
 const count=await page.evaluate(()=>window.__speech.spoken.length)
 await page.waitForTimeout(4300)
 assert.equal(await page.evaluate(()=>window.__speech.spoken.length),count,'Repeated polls must not reread a completed answer')
 await page.evaluate(()=>window.__speech.failOutput())
 await page.getByText(/自動読み上げをこのブラウザが制限/).waitFor()
 await page.getByRole('button',{name:'声で入力',exact:true}).click()
 await page.evaluate(()=>window.__speech.deny())
 await page.getByText(/ブラウザのマイク許可を確認/).waitFor()
 await page.getByRole('button',{name:'声で入力',exact:true}).click()
 const aborted=await page.evaluate(()=>window.__speech.aborts)
 await page.getByRole('button',{name:'条件',exact:true}).click()
 assert.ok(await page.evaluate(()=>window.__speech.aborts)>aborted,'Hidden AI panel must release the microphone')
 await page.getByRole('button',{name:'✳ AIと試す',exact:true}).click()
 // A later completed message must not hide an earlier streamed core answer's final update.
 const existing=await api('council'),last=Math.max(...existing.messages.map(m=>m.id))
 let streamDone=false
 const streamed={id:last+1,who:'core',label:'中心（検証用）',model:'voice-contract-test',text:'検証用のストリーム返答です。予想は未検証です。',done:false,kind:'chat',usage:null,usd:0,at:'test'}
 const follower={...streamed,id:last+2,who:'system',text:'後続メッセージの完了（検証用）',done:true}
 await page.route('**/api/council?since=*',async route=>{
  const r=await route.fetch(),body=await r.json(),since=Number(new URL(route.request().url()).searchParams.get('since'))
  const extra=[{...streamed,done:streamDone},follower].filter(m=>m.id>since||!m.done)
  await route.fulfill({response:r,json:{...body,messages:[...body.messages,...extra]}})
 })
 await page.getByText(streamed.text,{exact:true}).waitFor()
 streamDone=true
 await page.waitForFunction(()=>window.__speech.spoken.some(s=>s.text.includes('ストリーム返答')))
 await page.unrouteAll({behavior:'wait'})
 await page.reload();await page.locator('.lab-read-reply').first().waitFor();await page.waitForTimeout(500)
 assert.equal(await page.evaluate(()=>window.__speech.spoken.length),0,'Persisted opt-in must not read history on reload')
 await page.setViewportSize({width:390,height:844})
 await page.getByRole('button',{name:'声で入力',exact:true}).click()
 await page.evaluate(()=>window.__speech.result('声で入力している画面の動作確認です',false))
 await page.locator('.lab-voice-preview output').filter({hasText:'声で入力している画面の動作確認です'}).waitFor()
 await page.screenshot({path:artifacts+'/voice-mobile.png'})
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),390)
 const stage=await page.locator('.lab-stage').boundingBox()
 assert.ok(stage.y>=0&&stage.y+stage.height<844)
 const cancels=await page.evaluate(()=>window.__speech.aborts)
 await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'hidden'});document.dispatchEvent(new Event('visibilitychange'))})
 assert.ok(await page.evaluate(()=>window.__speech.aborts)>cancels)
 await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'visible'});document.dispatchEvent(new Event('visibilitychange'))})
 await api('council/external',{who:'claude-code',text:'画面へ戻ったあとの新しい返答です。これは音声機能の動作確認です。'})
 await page.waitForFunction(()=>window.__speech.spoken.some(s=>s.text.includes('画面へ戻ったあとの')))
 assert.deepEqual({info:await api('universes/'+u.id),frame:await frameHash(u.id)},before,'Voice must not change a physics frame or its parameters')
 assert.deepEqual(errors,[])
 await page.close()
 const unsupported=await browser.newPage()
 await unsupported.addInitScript(()=>{for(const key of ['SpeechRecognition','webkitSpeechRecognition','speechSynthesis','SpeechSynthesisUtterance'])Object.defineProperty(window,key,{value:undefined,configurable:true})})
 await unsupported.goto(base+'/#lab');await unsupported.getByRole('button',{name:'声で入力',exact:true}).waitFor()
 assert.ok(await unsupported.getByRole('button',{name:'声で入力',exact:true}).isDisabled())
 assert.ok(await unsupported.getByRole('checkbox',{name:'返答を自動で読み上げる',exact:true}).isDisabled())
 await unsupported.getByText(/このブラウザはマイクによる音声入力に対応/).waitFor();await unsupported.close()
 const insecure=await browser.newPage()
 await insecure.addInitScript(fakeSpeech)
 await insecure.addInitScript(()=>Object.defineProperty(window,'isSecureContext',{value:false,configurable:true}))
 await insecure.goto(base+'/#lab');await insecure.getByRole('button',{name:'声で入力',exact:true}).waitFor()
 assert.ok(await insecure.getByRole('button',{name:'声で入力',exact:true}).isDisabled())
 await insecure.getByText(/音声入力はHTTPSまたはlocalhost/).waitFor();await insecure.close()
 console.log(JSON.stringify({passed:['editable voice draft','interim text stays uncommitted','late final on stop','no duplicate recognition','manual speech and queue cancellation','new replies only and no replay on polls/reload','out-of-order streamed completion','autoplay denial feedback','microphone denial feedback','stop on tab/page hide','mobile UI','unsupported and insecure fallback','unchanged 3D solver and frame SHA256'],source:before.frame,scope:'Mocked browser speech events; real microphone/acoustic playback not verified'}))
}catch(error){
 if(!page.isClosed())await page.screenshot({path:artifacts+'/voice-check-failure.png'}).catch(()=>{})
 throw error
}finally{await browser.close()}
