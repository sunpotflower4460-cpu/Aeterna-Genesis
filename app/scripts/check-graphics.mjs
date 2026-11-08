// A fresh isolated lab, no external AI calls. 3D rendering first, 2D rendering second.
import {chromium} from 'playwright'
import assert from 'node:assert/strict'
import {mkdir} from 'node:fs/promises'
import {createHash} from 'node:crypto'
const base=process.env.LAB_TEST_URL||'http://127.0.0.1:18767'
const out=process.env.LAB_SCREENSHOT_DIR||'/tmp/aeterna-graphics-check'
await mkdir(out,{recursive:true})
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader']})
const page=await browser.newPage({viewport:{width:1400,height:1000},deviceScaleFactor:1,acceptDownloads:true})
const errors=[]
page.on('pageerror',e=>errors.push(e.message))
page.on('console',m=>{if(m.type()==='error'&&/shader|WebGL|GL_INVALID/i.test(m.text()))errors.push(m.text())})
const api=async(path,data)=>{
 const r=await page.request[data===undefined?'get':'post'](base+'/api/'+path,data===undefined?{}:{data})
 assert.ok(r.ok(),await r.text());return r.json()
}
async function frameHash(id,lens){
 const response=await fetch(`${base}/api/stream?u=${encodeURIComponent(id+':'+lens)}`)
 const reader=response.body.getReader(),decode=new TextDecoder();let text=''
 try{
  for(let i=0;i<100;i++){
   const {value,done}=await reader.read();if(done)break;text+=decode.decode(value,{stream:true})
   let at
   while((at=text.indexOf('\n\n'))>=0){
    const part=text.slice(0,at);text=text.slice(at+2)
    if(!part.startsWith('event: frame'))continue
    const data=JSON.parse(part.split('\n').find(l=>l.startsWith('data:')).slice(5))
    if(data.b64)return createHash('sha256').update(Buffer.from(data.b64,'base64')).digest('hex')
   }
  }
  throw new Error('No field frame arrived')
 }finally{await reader.cancel()}
}
const checksum=async(id,lens)=>({frame:await frameHash(id,lens),universe:await api('universes/'+id)})
const wait=()=>page.waitForTimeout(600)
try{
 assert.equal((await api('universes')).universes.length,0,'Use a fresh isolated lab server')
 const u=await api('universes',{white:'tdgl-3d',seed:2,play:false})
 await api(`universes/${u.id}/control`,{action:'step',n:100})
 await page.goto(base+'/#lab')
 await page.locator('.field-legend-ramp').first().waitFor()
 await wait()
 const before=await checksum(u.id,'density')
 await page.screenshot({path:out+'/3d-volume.png'})
 await page.getByRole('button',{name:'描画設定',exact:true}).click()
 await page.getByLabel('配色',{exact:true}).selectOption('ember')
 await page.getByLabel('描画品質',{exact:true}).selectOption('fine')
 await wait()
 await page.getByRole('button',{name:'描画設定を閉じる',exact:true}).click()
 await page.screenshot({path:out+'/3d-volume-ember.png'})
 await page.getByRole('button',{name:'描画設定',exact:true}).click()
 await page.getByRole('button',{name:'等値面',exact:true}).click()
 await page.getByRole('button',{name:'描画設定を閉じる',exact:true}).click()
 await wait();await page.screenshot({path:out+'/3d-isosurface.png'})
 await page.getByRole('button',{name:'描画設定',exact:true}).click()
 await page.getByRole('button',{name:'断面',exact:true}).click()
 await page.getByLabel('断面の向き',{exact:true}).selectOption('y')
 await page.getByLabel('断面の位置',{exact:true}).fill('0.62')
 await page.getByLabel('配色',{exact:true}).selectOption('ice')
 await page.getByRole('button',{name:'描画設定を閉じる',exact:true}).click()
 await wait();await page.screenshot({path:out+'/3d-slice.png'})
 await page.getByRole('button',{name:'条件',exact:true}).click()
 await page.getByRole('combobox',{name:'レンズ',exact:true}).selectOption('phase')
 await wait()
 await page.getByRole('button',{name:'✳ AIと試す',exact:true}).click()
 await page.screenshot({path:out+'/3d-phase.png'})
 // View quality, slices, palettes, phase encoding and camera all leave the solver and its source bytes alone.
 assert.deepEqual(await checksum(u.id,'density'),before)
 const download=page.waitForEvent('download')
 await page.getByRole('button',{name:'PNG保存 ↗',exact:true}).click()
 const png=await download
 assert.match(png.suggestedFilename(),/^aeterna-field-.*\.png$/)
 await png.saveAs(out+'/observation-export.png')
 await page.setViewportSize({width:390,height:844});await wait()
 await page.getByRole('button',{name:'✳ この実験について聞く',exact:true}).click()
 await wait();await page.screenshot({path:out+'/mobile-3d-question.png'})
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),390)
 const stage=await page.locator('.lab-stage').boundingBox(),question=await page.getByLabel('気になったことを質問する',{exact:true}).boundingBox()
 assert.ok(stage.y+stage.height<844&&question.y>=stage.y+stage.height&&question.y<844)
 // Shared rendering also works on the original recorded viewer: 3D first, then a real 2D vortex field.
 await page.setViewportSize({width:1400,height:1000})
 await page.getByRole('button',{name:'記録を見る ↗',exact:true}).click()
 await page.getByLabel('一時停止',{exact:true}).click()
 const time=page.getByRole('slider',{name:'時刻',exact:true})
 await page.waitForFunction(()=>Number(document.querySelector('.aq-range')?.max)>0)
 await time.fill(await time.getAttribute('max'))
 await time.press('End')
 await page.waitForFunction(()=>parseFloat(document.querySelector('.aq-time').textContent.replace('t=',''))>0)
 await page.getByRole('button',{name:'閉じる',exact:true}).click()
 await wait();await page.screenshot({path:out+'/recorded-3d.png'})
 await page.getByRole('button',{name:/2D 渦のペアが泳ぎだす/}).click()
 await page.getByRole('combobox',{name:'レンズ',exact:true}).selectOption('phase')
 await page.locator('.aq-overlay').waitFor({state:'hidden'})
 await page.waitForFunction(()=>Number(document.querySelector('.aq-range')?.max)>0)
 await time.fill(await time.getAttribute('max'))
 await time.press('End')
 await page.waitForFunction(()=>parseFloat(document.querySelector('.aq-time').textContent.replace('t=',''))>0)
 await wait();await page.screenshot({path:out+'/recorded-2d-phase.png'})
 await page.goto(base+'/#lab')
 // The 2D run is separate; relief is explicitly a view encoding of a 2D scalar, never a 3D claim.
 await page.request.delete(base+'/api/universes/'+u.id)
 const two=await api('universes',{white:'cgl',seed:4,play:false})
 await api(`universes/${two.id}/control`,{action:'step',n:8})
 await page.setViewportSize({width:1400,height:1000});await wait()
 await page.reload();await page.locator('.field-legend-ramp').first().waitFor();await wait()
 const twoBefore=await checksum(two.id,'phase')
 await page.getByRole('button',{name:'描画設定',exact:true}).click()
 await page.getByLabel('等高線（表示範囲の10等分）',{exact:true}).check()
 await page.getByRole('button',{name:'描画設定を閉じる',exact:true}).click()
 await wait();await page.screenshot({path:out+'/2d-phase-contours.png'})
 assert.deepEqual(await checksum(two.id,'phase'),twoBefore)
 assert.deepEqual(errors,[])
 console.log(JSON.stringify({passed:['3D volume','measured isosurface','palette and quality','3D slice and position','circular phase rendering','unchanged solver state and raw frame SHA256','PNG metadata export','phone field with question','2D circular phase and contours','2D raw frame SHA256 unchanged','recorded 3D and 2D viewer','no shader or page errors'],source:before.frame}))
}finally{await browser.close()}
