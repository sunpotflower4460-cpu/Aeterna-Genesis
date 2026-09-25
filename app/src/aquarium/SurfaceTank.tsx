import { useEffect, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import type { FrameSource, Transfer } from './types'

// 2D whites are shown as a water surface inside the tank: colour = the measured lens, height = the same
// normalized value (flat for cyclic phase, which has no height). Two neighbouring frames are blended on the GPU.
// Display only: the surface is a view of recorded values, not extra physics.

const VERT = /* glsl */ `
  uniform sampler2D uA; uniform sampler2D uB; uniform float uMix; uniform vec2 uAffA; uniform vec2 uAffB; uniform float uHeight; uniform int uMode;
  out float vVal; out vec2 vUv;
  float h(float v) { return uMode == 2 ? 0.5 : v; }  // cyclic phase has no meaningful height
  void main() {
    vUv = uv;
    float v = clamp(mix(texture(uA, uv).r * uAffA.x + uAffA.y, texture(uB, uv).r * uAffB.x + uAffB.y, uMix), 0.0, 1.0);
    vVal = v;
    vec3 p = position;
    p.z += (h(v) - 0.5) * uHeight;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  }`

const FRAG = /* glsl */ `
  precision highp float;
  in float vVal; in vec2 vUv; out vec4 outColor; uniform int uMode;
  vec3 ramp(float t) {
    t = clamp(t, 0.0, 1.0);
    vec3 a = vec3(0.02, 0.05, 0.14), b = vec3(0.05, 0.35, 0.5), c = vec3(0.31, 0.89, 0.88), e = vec3(0.92, 0.99, 1.0);
    if (t < 0.35) return mix(a, b, t / 0.35);
    if (t < 0.65) return mix(b, c, (t - 0.35) / 0.3);
    return mix(c, e, (t - 0.65) / 0.35);
  }
  vec3 hue(float h) {
    vec3 k = mod(vec3(0.0, 8.0, 4.0) + h * 12.0, 12.0);
    return 0.56 - 0.72 * 0.44 * clamp(min(k - 3.0, 9.0 - k), -1.0, 1.0);
  }
  vec3 diverg(float t) {
    return t < 0.5 ? mix(vec3(0.13, 0.4, 0.67), vec3(0.95), t * 2.0) : mix(vec3(0.95), vec3(0.7, 0.1, 0.17), t * 2.0 - 1.0);
  }
  void main() {
    vec3 c = uMode == 2 ? hue(vVal) : (uMode == 3 ? diverg(vVal) : ramp(uMode == 1 ? 1.0 - vVal : vVal));
    outColor = vec4(c, 0.96);
  }`

const MODE: Record<Transfer, number> = { high: 0, low: 1, cyclic: 2, diverging: 3 }

function makeTexture(grid: number[]): THREE.DataTexture {
  const [ny, nx] = grid
  const tex = new THREE.DataTexture(new Uint8Array(nx * ny), nx, ny, THREE.RedFormat, THREE.UnsignedByteType)
  tex.minFilter = THREE.LinearFilter
  tex.magFilter = THREE.LinearFilter
  tex.unpackAlignment = 1
  return tex
}

export default function SurfaceTank({ src, transfer, clock, relief }: {
  src: FrameSource
  transfer: Transfer
  clock: React.MutableRefObject<number>
  relief: number
}) {
  const gridKey = src.grid.join('x')
  const tex = useMemo(() => [makeTexture(src.grid), makeTexture(src.grid)] as const, [gridKey])
  const loaded = useRef<[number, number]>([-1, -1])
  const segs = Math.min(255, Math.max(src.grid[0], src.grid[1]) * 2)
  const material = useMemo(() => new THREE.ShaderMaterial({
    glslVersion: THREE.GLSL3, vertexShader: VERT, fragmentShader: FRAG, transparent: true,
    side: THREE.DoubleSide,
    uniforms: { uA: { value: tex[0] }, uB: { value: tex[1] }, uMix: { value: 0 }, uHeight: { value: relief },
      uAffA: { value: new THREE.Vector2(1, 0) }, uAffB: { value: new THREE.Vector2(1, 0) },
      uMode: { value: MODE[transfer] } },
  }), [tex])

  useEffect(() => { loaded.current = [-1, -1] }, [src])
  useEffect(() => () => { tex[0].dispose(); tex[1].dispose(); material.dispose() }, [tex, material])

  const upload = (slot: 0 | 1, frame: number) => {
    const k = src.key(frame)
    if (loaded.current[slot] === k) return
    const d = src.data(frame)
    if (d.length !== (tex[slot].image.data as Uint8Array).length) return   // grid changed; new textures follow
    ;(tex[slot].image.data as Uint8Array).set(d)
    tex[slot].needsUpdate = true
    loaded.current[slot] = k
  }

  useFrame(() => {
    if (src.count < 1) return
    const pos = Math.min(Math.max(clock.current, 0), src.count - 1)
    const f0 = Math.floor(pos)
    const f1 = Math.min(f0 + 1, src.count - 1)
    upload(0, f0)
    upload(1, f1)
    const u = material.uniforms
    u.uMix.value = pos - f0
    u.uAffA.value.set(...src.affine(f0))
    u.uAffB.value.set(...src.affine(f1))
    u.uHeight.value = relief
    u.uMode.value = MODE[transfer]
  })

  return (
    <mesh material={material} rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.15, 0]}>
      <planeGeometry args={[1, 1, segs, segs]} />
    </mesh>
  )
}
