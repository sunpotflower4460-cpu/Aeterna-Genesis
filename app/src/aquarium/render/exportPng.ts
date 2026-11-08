import { colorCss, type Appearance } from './appearance'
import type { Transfer } from '../types'
export interface CaptureLegend { label:string;lo:number;hi:number;transfer:Transfer }
/** Capture only pixels already rendered from the field. The footer identifies the view transformations. */
export async function exportFieldPng(canvas:HTMLCanvasElement, legends:CaptureLegend[], appearance:Appearance, view:{threshold:number;density:number;relief:number}):Promise<void> {
  const out=document.createElement('canvas')
  const width=Math.max(canvas.width,900),scale=width/canvas.width
  out.width=width;out.height=Math.round(canvas.height*scale)+142+legends.length*46
  const ctx=out.getContext('2d')
  if(!ctx)throw new Error('画像の保存をこのブラウザで開始できませんでした')
  ctx.fillStyle='#080e16';ctx.fillRect(0,0,out.width,out.height)
  ctx.drawImage(canvas,0,0,width,canvas.height*scale)
  let y=Math.round(canvas.height*scale)+25
  ctx.fillStyle='#d7e9ed';ctx.font='17px system-ui';ctx.fillText('Aeterna Genesis · field observation',24,y)
  y+=22;ctx.font='11px system-ui';ctx.fillStyle='#9aafc0'
  ctx.fillText(`Display only · 3D view ${appearance.mode} · ${appearance.palette} · ${appearance.quality} · shading ${appearance.shading?'on':'off'} · time interpolation ${appearance.interpolate?'on':'off'}`,24,y)
  y+=18;ctx.fillText(`Threshold ${view.threshold} | opacity ${view.density} | 2D relief ${view.relief} | slice ${appearance.axis.toUpperCase()}=${appearance.slice}`,24,y)
  y+=18;ctx.fillText('uint8 + spatial interpolation; displayed time may lag the solver by one frame. Lighting is a reading aid.',24,y)
  if(legends.some(l=>l.transfer==='cyclic')){y+=18;ctx.fillText('Phase uses circular averaging; indeterminate average directions are faint (not a defect measurement).',24,y)}
  for(const legend of legends){
    y+=28;ctx.fillStyle='#c8dbe5';ctx.fillText(legend.label,24,y)
    const left=width-250,barWidth=200
    for(let i=0;i<barWidth;i++){ctx.fillStyle=colorCss(i/(barWidth-1),legend.transfer,appearance.palette);ctx.fillRect(left+i,y-10,1,7)}
    ctx.fillStyle='#9aafc0';ctx.fillText(Number(legend.lo.toPrecision(4)).toString(),left,y+12)
    ctx.textAlign='right';ctx.fillText(Number(legend.hi.toPrecision(4)).toString(),left+barWidth,y+12);ctx.textAlign='left'
  }
  const blob=await new Promise<Blob|null>(resolve=>out.toBlob(resolve,'image/png'))
  if(!blob)throw new Error('PNGの作成に失敗しました')
  const url=URL.createObjectURL(blob),link=document.createElement('a')
  link.href=url;link.download=`aeterna-field-${new Date().toISOString().replace(/[:.]/g,'-')}.png`;link.click()
  setTimeout(()=>URL.revokeObjectURL(url),10000)
}
