import { useMemo, useEffect, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import type { DecodedLens } from '../lib/types'
import { lensColor, lensAlpha } from '../lib/colormap'
import type { ViewSettings } from '../store'

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

function positions(grid: number[]): Float32Array {
  const S = 2.0
  if (grid.length === 2) {
    const [a, b] = grid
    const p = new Float32Array(a * b * 3)
    let n = 0
    for (let i = 0; i < a; i++) for (let j = 0; j < b; j++) {
      p[n++] = (i / (a - 1) - 0.5) * S
      p[n++] = (j / (b - 1) - 0.5) * S
      p[n++] = 0
    }
    return p
  }
  const [a, b, c] = grid
  const p = new Float32Array(a * b * c * 3)
  let n = 0
  for (let i = 0; i < a; i++) for (let j = 0; j < b; j++) for (let k = 0; k < c; k++) {
    p[n++] = (i / (a - 1) - 0.5) * S
    p[n++] = (k / (c - 1) - 0.5) * S
    p[n++] = (j / (b - 1) - 0.5) * S
  }
  return p
}

function FieldPoints({ lens, frame, view }: { lens: DecodedLens; frame: number; view: ViewSettings }) {
  const stride = lens.grid.reduce((a, b) => a * b, 1)
  const obj = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions(lens.grid), 3))
    geo.setAttribute('acolor', new THREE.BufferAttribute(new Float32Array(stride * 3), 3))
    geo.setAttribute('aalpha', new THREE.BufferAttribute(new Float32Array(stride), 1))
    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT, fragmentShader: FRAG,
      uniforms: { uSize: { value: 4 } },
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    })
    return new THREE.Points(geo, mat)
  }, [lens.grid.join(','), stride])

  useEffect(() => () => { obj.geometry.dispose(); (obj.material as THREE.Material).dispose() }, [obj])

  useEffect(() => {
    const f = Math.min(frame, lens.nframes - 1)
    const off = f * stride
    const col = obj.geometry.getAttribute('acolor') as THREE.BufferAttribute
    const alp = obj.geometry.getAttribute('aalpha') as THREE.BufferAttribute
    const ca = col.array as Float32Array
    const aa = alp.array as Float32Array
    // volumes overlap ~grid-depth layers additively; scale per-point alpha down so the core glows
    // instead of clipping to white (2D sheets barely overlap, so keep them brighter)
    const vscale = lens.grid.length === 3 ? 0.32 : 0.85
    for (let i = 0; i < stride; i++) {
      const v = lens.norm[off + i]
      const [r, g, b] = lensColor(v, lens.cyclic)
      ca[i * 3] = r; ca[i * 3 + 1] = g; ca[i * 3 + 2] = b
      const below = !lens.cyclic && v < view.threshold
      aa[i] = below ? 0 : lensAlpha(v, lens.cyclic) * view.opacity * vscale
    }
    col.needsUpdate = true
    alp.needsUpdate = true
    const mat = obj.material as THREE.ShaderMaterial
    mat.uniforms.uSize.value = 1.4 + view.glow * 2.0
  }, [frame, lens, stride, view.threshold, view.opacity, view.glow, obj])

  return <primitive object={obj} />
}

function Spin() {
  const g = useRef<THREE.Group>(null)
  useFrame((_, dt) => { if (g.current) g.current.rotation.y += dt * 0.06 })
  return <group ref={g} />
}

export default function Viewport({ lens, frame, view, is3d }:
  { lens: DecodedLens | null; frame: number; view: ViewSettings; is3d: boolean }) {
  return (
    <Canvas camera={{ position: is3d ? [2.6, 1.8, 2.6] : [0, 0, 3.1], fov: 42 }} dpr={[1, 2]}
      gl={{ antialias: true, alpha: true }} style={{ position: 'absolute', inset: 0 }}>
      <color attach="background" args={['#04070e']} />
      <fog attach="fog" args={['#04070e', 5, 11]} />
      {lens && <FieldPoints lens={lens} frame={frame} view={view} />}
      <OrbitControls enablePan={false} enableDamping dampingFactor={0.08}
        minDistance={1.6} maxDistance={7} autoRotate={is3d} autoRotateSpeed={0.35} />
      <Spin />
    </Canvas>
  )
}
