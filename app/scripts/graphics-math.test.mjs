import test from 'node:test'
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { textureBytes, makeFieldTexture, uploadField } from '../src/aquarium/render/texture.ts'
import { displayColor, legendGradient } from '../src/aquarium/render/appearance.ts'
const hash=data=>createHash('sha256').update(data).digest('hex')

test('circle interpolation preserves the phase seam rather than inventing a half-cycle',()=>{
  const bytes=textureBytes(new Uint8Array([1,254]),true)
  const x=(bytes[0]+bytes[2])/255-1,y=(bytes[1]+bytes[3])/255-1
  const phase=(Math.atan2(y,x)/Math.PI/2+1)%1
  assert.ok(phase<0.02 || phase>0.98)
  const opposite=textureBytes(new Uint8Array([0,128]),true)
  const ambiguous=Math.hypot((opposite[0]+opposite[2])/255-1,(opposite[1]+opposite[3])/255-1)
  assert.ok(ambiguous<0.015,'Opposing phase averages must be masked by the shader')
})
test('scalar and circle uploads leave source evidence unchanged and reject a wrong grid',()=>{
  const evidence=Uint8Array.from({length:64},(_,i)=>i*4),before=hash(evidence)
  for(const cyclic of [false,true]){
    const texture=makeFieldTexture([4,4,4],cyclic)
    assert.ok(uploadField(texture,evidence,cyclic))
    const frame=new Uint8Array(texture.image.data)
    assert.equal(uploadField(texture,new Uint8Array(2),cyclic),false)
    assert.deepEqual(texture.image.data,frame)
    assert.notEqual(texture.image.data.buffer,evidence.buffer)
    texture.dispose()
  }
  assert.equal(hash(evidence),before)
})
test('sequential palettes stay finite and monotonic in weighted RGB luma; cyclic endpoints agree',()=>{
  for(const palette of ['ice','ember','mono'])for(const transfer of ['high','low']){
    let previous=null
    for(let i=0;i<=255;i++){
      const rgb=displayColor(i/255,transfer,palette)
      assert.ok(rgb.every(v=>Number.isFinite(v)&&v>=0&&v<=1))
      const luminance=rgb[0]*0.2126+rgb[1]*0.7152+rgb[2]*0.0722
      const direction=transfer==='low'?-1:1
      if(previous!==null)assert.ok((luminance-previous)*direction>=-1e-8)
      previous=luminance
    }
  }
  assert.deepEqual(displayColor(0,'cyclic','ice'),displayColor(1,'cyclic','ice'))
  assert.match(legendGradient('diverging','ice'),/linear-gradient/)
})
