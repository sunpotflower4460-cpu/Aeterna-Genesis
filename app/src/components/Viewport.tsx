import { useMemo, useEffect, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import type { DecodedLens } from '../lib/types'
import { lensColor, lensAlpha } from '../lib/colormap'
import type { ViewSettings } from '../store'

const REDUCED = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

function hasWebGL2(): boolean {
  try { return !!document.createElement('canvas').getContext('webgl2') } catch { return false }
}

const VERT = `
  attribute vec3 acolor; attribute float aalpha;
  uniform float uSize; varying vec3 vColor; varying float vAlpha;
  void main(){
    vColor = acolor; vAlpha = aalpha;
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    gl_Position = projectionMatrix * mv;
    gl_PointSize = uSize * (120.0 / max(-mv.z, 1.0));
  }`
const FRAG = `
  varying vec3 vColor; varying float vAlpha;
  void main(){
    vec2 d = gl_PointCoord - vec2(0.5);
    float r = length(d);
    if(r > 0.5) discard;
    float a = pow(1.0 - r*2.0, 1.4) * vAlpha;
    gl_FragColor = vec4(vColor, a);
  }`

// LOD: for dense 3D volumes, keep a strided subset when quality < 1 (low-end / reduced load).
function lodIndices(grid: number[], quality: number): Uint32Array | null {
  if (grid.length < 3 || quality >= 0.99) return null
  const total = grid.reduce((a, b) => a * b, 1)
  const every = Math.max(1, Math.round(1 / quality))
  if (every === 1) return null
  const out: number[] = []
  for (let i = 0; i < total; i += every) out.push(i)
  return new Uint32Array(out)
}

function posFromIndex(grid: number[], flat: number, S: number): [number, number, number] {
  if (grid.length === 2) {
    const [a, b] = grid
    const i = Math.floor(flat / b), j = flat % b
    return [(i / (a - 1) - 0.5) * S, (j / (b - 1) - 0.5) * S, 0]
  }
  const [a, b, c] = grid
  const i = Math.floor(flat / (b * c)), j = Math.floor((flat % (b * c)) / c), k = flat % c
  return [(i / (a - 1) - 0.5) * S, (k / (c - 1) - 0.5) * S, (j / (b - 1) - 0.5) * S]
}

function FieldPoints({ lens, view, playing, speed, clock, nframes, onFrame }: {
  lens: DecodedLens; view: ViewSettings; playing: boolean; speed: number; clock: React.MutableRefObject<number>
  nframes: number; onFrame: (i: number) => void
}) {
  const stride = lens.grid.reduce((a, b) => a * b, 1)
  const idx = useMemo(() => lodIndices(lens.grid, view.quality), [lens.grid.join(','), view.quality])
  const lastInt = useRef(-1)

  const obj = useMemo(() => {
    const count = idx ? idx.length : stride
    const S = 2
    const pos = new Float32Array(count * 3)
    for (let n = 0; n < count; n++) {
      const flat = idx ? idx[n] : n
      const [x, y, z] = posFromIndex(lens.grid, flat, S)
      pos[n * 3] = x; pos[n * 3 + 1] = y; pos[n * 3 + 2] = z
    }
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    geo.setAttribute('acolor', new THREE.BufferAttribute(new Float32Array(count * 3), 3))
    geo.setAttribute('aalpha', new THREE.BufferAttribute(new Float32Array(count), 1))
    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT, fragmentShader: FRAG, uniforms: { uSize: { value: 3 } },
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    })
    return new THREE.Points(geo, mat)
  }, [lens.grid.join(','), lens.name, stride, idx])

  useEffect(() => () => { obj.geometry.dispose(); (obj.material as THREE.Material).dispose() }, [obj])

  useFrame((_, dt) => {
    if (playing && nframes > 1) clock.current = (clock.current + dt * 3.2 * speed) % nframes
    const t = Math.min(clock.current, nframes - 1e-4)
    const f0 = Math.floor(t)
    const f1 = (f0 + 1) % nframes
    const frac = t - f0
    const off0 = f0 * stride, off1 = f1 * stride
    const count = idx ? idx.length : stride
    const col = obj.geometry.getAttribute('acolor') as THREE.BufferAttribute
    const alp = obj.geometry.getAttribute('aalpha') as THREE.BufferAttribute
    const ca = col.array as Float32Array, aa = alp.array as Float32Array
    const vscale = lens.grid.length === 3 ? 0.32 : 0.85
    for (let n = 0; n < count; n++) {
      const c = idx ? idx[n] : n
      const v0 = lens.norm[off0 + c]
      const v = lens.cyclic ? v0 : v0 + (lens.norm[off1 + c] - v0) * frac // interpolate linear; snap cyclic
      const [r, g, b] = lensColor(v, lens.cyclic)
      ca[n * 3] = r; ca[n * 3 + 1] = g; ca[n * 3 + 2] = b
      aa[n] = (!lens.cyclic && v < view.threshold) ? 0 : lensAlpha(v, lens.cyclic) * view.opacity * vscale
    }
    col.needsUpdate = true; alp.needsUpdate = true
    ;(obj.material as THREE.ShaderMaterial).uniforms.uSize.value = 1.4 + view.glow * 2.0
    const fi = Math.floor(t)
    if (fi !== lastInt.current) { lastInt.current = fi; onFrame(fi) }
  })

  return <primitive object={obj} />
}

export default function Viewport({ lens, view, is3d, playing, speed, clock, nframes, onFrame }: {
  lens: DecodedLens | null; view: ViewSettings; is3d: boolean; playing: boolean; speed: number
  clock: React.MutableRefObject<number>; nframes: number; onFrame: (i: number) => void
}) {
  if (!hasWebGL2()) {
    return (
      <div className="mono muted" style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', textAlign: 'center', padding: 24, fontSize: 12.5 }}>
        WebGL2 が使えない環境です。<br />対応ブラウザ（GPU 有効）で 3D 表示できます。
      </div>
    )
  }
  return (
    <Canvas camera={{ position: is3d ? [2.6, 1.8, 2.6] : [0, 0, 3.1], fov: 42 }} dpr={[1, Math.min(2, Math.round(1 + view.quality))]}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }} style={{ position: 'absolute', inset: 0 }}>
      <color attach="background" args={['#04070e']} />
      <fog attach="fog" args={['#04070e', 5, 11]} />
      {lens && <FieldPoints lens={lens} view={view} playing={playing} speed={speed} clock={clock} nframes={nframes} onFrame={onFrame} />}
      <OrbitControls enablePan={false} enableDamping dampingFactor={0.08} minDistance={1.6} maxDistance={7}
        autoRotate={is3d && !REDUCED} autoRotateSpeed={0.3} />
    </Canvas>
  )
}
