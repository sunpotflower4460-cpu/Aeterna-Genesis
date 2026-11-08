import test from 'node:test'
import assert from 'node:assert/strict'
import {speechText,speechChunks} from '../src/lab/speechText.ts'

test('speech retains scientific qualifiers, signs, variable names and products',()=>{
 const source='# 未検証の予想\n**測定**: mean_amp=0.002、差は -0.3。x*y は仮説。\n[出典](https://example.com/paper)'
 const result=speechText(source)
 for(const value of ['未検証の予想','測定','mean_amp=0.002','-0.3','x*y','仮説','出典'])assert.ok(result.includes(value),value)
 assert.ok(!result.includes('https://'))
 assert.equal(speechText('区間 [0,1](境界を含む)'),'区間 [0,1](境界を含む)')
})
test('fenced code omission is explicitly announced',()=>{
 const original='予想（未検証）です。\n```json\n{"noise":0.002}\n```\n測ってから判断します。'
 const result=speechText(original)
 assert.ok(result.includes('コードや入力例は画面で確認できます。'))
 assert.ok(result.includes('予想（未検証）'))
 assert.ok(result.includes('測ってから判断'))
})
test('long Japanese speech is bounded without breaking surrogate pairs or normal numeric atoms',()=>{
 const chunks=speechChunks('あ'.repeat(98)+'0.002、mean_amp=-1.25e-7。'+'🌊'.repeat(160)+'。')
 assert.ok(chunks.length>2)
 assert.ok(chunks.every(c=>Array.from(c).length<=100))
 assert.ok(chunks.some(c=>c.includes('0.002')))
 assert.ok(chunks.some(c=>c.includes('mean_amp=-1.25e-7')))
 assert.ok(chunks.every(c=>!/(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])/u.test(c)))
})
test('empty speech does not enqueue audio',()=>{
 assert.deepEqual(speechChunks(' \n\n '),[])
})
