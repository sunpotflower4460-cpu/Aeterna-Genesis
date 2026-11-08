import type { Transfer } from '../types'
import { legendGradient, type Appearance } from './appearance'
export function formatBound(value:number):string {
  if(!Number.isFinite(value))return '—'
  return Number(value.toPrecision(3)).toString()
}
export default function FieldLegend({ transfer,palette,lo,hi,label,adaptive=false }: {
  transfer:Transfer;palette:Appearance['palette'];lo:number;hi:number;label:string;adaptive?:boolean
}) {
  return <div className="field-legend" aria-label={`${label}の色の凡例`}>
    <div className="field-legend-title"><span>{label}</span><small>{transfer==='cyclic'?'循環補間 · 不定部は薄く':adaptive?'相対値 · 各コマで再配色':'固定の色範囲'}</small></div>
    <div className="field-legend-ramp" style={{background:legendGradient(transfer,palette)}}/>
    <div className="field-legend-bounds mono"><span>{formatBound(adaptive ? 0 : lo)}</span><span>{transfer==='cyclic'?'位相 rad · 循環':transfer==='low'?'小さい値を表示':'大きさ →'}</span><span>{formatBound(adaptive ? 1 : hi)}</span></div>
  </div>
}
