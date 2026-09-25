import { useEffect, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import type { TankLens, Transfer } from './types'

// 2D whites are shown as a water surface inside the tank: colour = the measured lens, height = the same
// normalized value (flat for cyclic phase, which has no height). Two neighbouring frames are blended on the GPU.
// Display only: the surface is a view of recorded values, not extra physics.

const VERT = /* glsl */ `
  uniform sampler2D uA; uniform sampler2D uB; uniform float uMix; uniform float uHeight; uniform int uMode;
  out float vVal; out vec2 vUv;
  float h(float v) { return uMode == 2 ? 0.5 : v; }  // cyclic phase has no meaningful height
  void main() {
    vUv = uv;
    float v = mix(texture(uA, uv).r, texture(uB, uv).r, uMix);
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

export default function SurfaceTank({ lens, transfer, clock, relief }: {
  lens: TankLens
  transfer: Transfer
  clock: React.MutableRefObject<number>
  relief: number
}) {
  const stride = lens.grid[0] * lens.grid[1]
  const tex = useMemo(() => [makeTexture(lens.grid), makeTexture(lens.grid)] as const, [lens])
  const loaded = useRef<[number, number]>([-1, -1])
  const segs = Math.min(255, Math.max(lens.grid[0], lens.grid[1]) * 2)
  const material = useMemo(() => new THREE.ShaderMaterial({
    glslVersion: THREE.GLSL3, vertexShader: VERT, fragmentShader: FRAG, transparent: true,
    side: THREE.DoubleSide,
    uniforms: { uA: { value: tex[0] }, uB: { value: tex[1] }, uMix: { value: 0 }, uHeight: { value: relief },
      uMode: { value: MODE[transfer] } },
  }), [tex])

  useEffect(() => () => { tex[0].dispose(); tex[1].dispose(); material.dispose() }, [tex, material])

  const upload = (slot: 0 | 1, frame: number) => {
    if (loaded.current[slot] === frame) return
    ;(tex[slot].image.data as Uint8Array).set(lens.frames.subarray(frame * stride, (frame + 1) * stride))
    tex[slot].needsUpdate = true
    loaded.current[slot] = frame
  }

  useFrame(() => {
    const pos = Math.min(Math.max(clock.current, 0), lens.nframes - 1)
    const f0 = Math.floor(pos)
    upload(0, f0)
    upload(1, Math.min(f0 + 1, lens.nframes - 1))
    material.uniforms.uMix.value = pos - f0
    material.uniforms.uHeight.value = relief
    material.uniforms.uMode.value = MODE[transfer]
  })

  return (
    <mesh material={material} rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.15, 0]}>
      <planeGeometry args={[1, 1, segs, segs]} />
    </mesh>
  )
}
