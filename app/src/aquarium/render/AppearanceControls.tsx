import type { Appearance } from './appearance'

export default function AppearanceControls({ value, onChange, dimension }: {
  value:Appearance;onChange:(next:Appearance)=>void;dimension:2|3
}) {
  const set=<K extends keyof Appearance>(key:K,next:Appearance[K])=>onChange({...value,[key]:next})
  return <div className="field-appearance">
    <div className="field-control-heading"><b>描画の設定</b><span>表示だけを変更</span></div>
    {dimension===3&&<>
      <div className="field-segment" aria-label="3Dの表示方法">
        <button type="button" aria-pressed={value.mode==='volume'} onClick={()=>set('mode','volume')}>体積</button>
        <button type="button" aria-pressed={value.mode==='surface'} onClick={()=>set('mode','surface')}>等値面</button>
        <button type="button" aria-pressed={value.mode==='slice'} onClick={()=>set('mode','slice')}>断面</button>
      </div>
      {value.mode==='slice'&&<div className="field-slice-controls">
        <label>断面の向き<select aria-label="断面の向き" value={value.axis} onChange={e=>set('axis',e.target.value as Appearance['axis'])}><option value="x">X に垂直</option><option value="y">Y に垂直</option><option value="z">Z に垂直</option></select></label>
        <label>断面の位置 <output>{Math.round(value.slice*100)}%</output><input aria-label="断面の位置" type="range" min={0.01} max={0.99} step={0.01} value={value.slice} onChange={e=>set('slice',Number(e.target.value))}/></label>
      </div>}
    </>}
    <label>配色<select aria-label="配色" value={value.palette} onChange={e=>set('palette',e.target.value as Appearance['palette'])}><option value="ice">氷青 / 淡金</option><option value="ember">琥珀</option><option value="mono">モノクロ</option></select></label>
    <p>位相は循環色、正負の量は青と赤を使います。</p>
    {dimension===3&&<label>描画品質<select aria-label="描画品質" value={value.quality} onChange={e=>set('quality',e.target.value as Appearance['quality'])}><option value="draft">軽量</option><option value="balanced">標準</option><option value="fine">精細</option></select></label>}
    <label className="field-check"><input type="checkbox" checked={value.shading} onChange={e=>set('shading',e.target.checked)}/>形を読みやすくする陰影</label>
    {dimension===2&&<label className="field-check"><input type="checkbox" checked={value.contours} onChange={e=>set('contours',e.target.checked)}/>等高線（表示範囲の10等分）</label>}
    <label className="field-check"><input type="checkbox" checked={value.guides} onChange={e=>set('guides',e.target.checked)}/>座標ガイド</label>
    <label className="field-check"><input type="checkbox" checked={value.interpolate} onChange={e=>set('interpolate',e.target.checked)}/>記録フレーム間を補間</label>
    <p>等値面は「しきい」と同じ値を持つ面です。陰影・透明度は読み取りの補助です。光・壁・粒子の物理計算ではありません。断面は3D場の一平面、2Dの起伏は値の高さ表現です。位相の平均方向が定まらない所は薄く表示し、欠陥の判定とは区別します。</p>
  </div>
}
