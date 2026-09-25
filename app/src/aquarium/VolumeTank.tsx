import { useEffect, useMemo, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import * as THREE from 'three'
import type { FrameSource, Transfer } from './types'

// Volume raymarcher: the recorded 3D field is uploaded as uint8 Data3DTextures (two neighbouring
// frames, blended in the shader for smooth playback). Display only -- it reads the measured values
// and never alters them; the transfer function only chooses which values glow.

const VERT = /* glsl */ `
  out vec3 vObj;
  void main() {
    vObj = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }`

const FRAG = /* glsl */ `
  precision highp float;
  precision highp sampler3D;
  in vec3 vObj;
  out vec4 outColor;
  uniform sampler3D uA;
  uniform sampler3D uB;
  uniform float uMix;
  uniform vec2 uAffA;      // display affine per frame: v -> a*v + b
  uniform vec2 uAffB;
  uniform vec3 uCam;        // camera position in object space
  uniform int uMode;        // 0 high, 1 low, 2 cyclic, 3 diverging
  uniform float uThr;       // [0,1] where the glow starts
  uniform float uDensity;   // opacity scale
  uniform float uSteps;

  vec2 hitBox(vec3 o, vec3 d) {
    vec3 inv = 1.0 / d;
    vec3 t0 = (vec3(-0.5) - o) * inv;
    vec3 t1 = (vec3(0.5) - o) * inv;
    vec3 tmin = min(t0, t1), tmax = max(t0, t1);
    return vec2(max(max(tmin.x, tmin.y), tmin.z), min(min(tmax.x, tmax.y), tmax.z));
  }
  vec3 ramp(float t) {                       // ice ramp (matches Observatory)
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
    vec3 rd = normalize(vObj - uCam);
    vec2 t = hitBox(uCam, rd);
    t.x = max(t.x, 0.0);
    if (t.x >= t.y) discard;
    float dt = 1.7320508 / uSteps;
    vec4 acc = vec4(0.0);
    for (int i = 0; i < 400; i++) {
      float s = t.x + (float(i) + 0.5) * dt;
      if (s > t.y || acc.a > 0.97) break;
      vec3 q = uCam + rd * s + 0.5;
      float v = clamp(mix(texture(uA, q).r * uAffA.x + uAffA.y, texture(uB, q).r * uAffB.x + uAffB.y, uMix), 0.0, 1.0);
      float w; vec3 col;
      if (uMode == 0) { w = smoothstep(uThr, 1.0, v); col = ramp(v); }
      else if (uMode == 1) { w = 1.0 - smoothstep(0.0, uThr, v); col = mix(vec3(1.0, 0.85, 0.45), vec3(0.3, 0.9, 1.0), v / max(uThr, 1e-3)); }
      else if (uMode == 2) { w = 0.35 * uThr; col = hue(v); }
      else { w = smoothstep(uThr, 0.5, abs(v - 0.5)); col = diverg(v); }
      float a = clamp(w * uDensity * dt * 60.0, 0.0, 1.0);
      acc.rgb += (1.0 - acc.a) * a * col;
      acc.a += (1.0 - acc.a) * a;
    }
    if (acc.a < 0.004) discard;
    outColor = vec4(acc.rgb, acc.a);
  }`

const MODE: Record<Transfer, number> = { high: 0, low: 1, cyclic: 2, diverging: 3 }

function makeTexture(grid: number[]): THREE.Data3DTexture {
  const [nz, ny, nx] = grid
  const tex = new THREE.Data3DTexture(new Uint8Array(nx * ny * nz), nx, ny, nz)
  tex.format = THREE.RedFormat
  tex.type = THREE.UnsignedByteType
  tex.minFilter = THREE.LinearFilter
  tex.magFilter = THREE.LinearFilter
  tex.unpackAlignment = 1
  tex.wrapS = tex.wrapT = tex.wrapR = THREE.ClampToEdgeWrapping
  return tex
}

export default function VolumeTank({ src, transfer, clock, threshold, density }: {
  src: FrameSource
  transfer: Transfer
  clock: React.MutableRefObject<number>   // continuous frame position, driven by the parent
  threshold: number
  density: number
}) {
  const mesh = useRef<THREE.Mesh>(null)
  const { camera } = useThree()
  const gridKey = src.grid.join('x')
  const tex = useMemo(() => [makeTexture(src.grid), makeTexture(src.grid)] as const, [gridKey])
  const loaded = useRef<[number, number]>([-1, -1])
  const material = useMemo(() => new THREE.ShaderMaterial({
    glslVersion: THREE.GLSL3,
    vertexShader: VERT,
    fragmentShader: FRAG,
    transparent: true,
    depthWrite: false,
    side: THREE.BackSide,
    uniforms: {
      uA: { value: tex[0] }, uB: { value: tex[1] }, uMix: { value: 0 }, uCam: { value: new THREE.Vector3() },
      uAffA: { value: new THREE.Vector2(1, 0) }, uAffB: { value: new THREE.Vector2(1, 0) },
      uMode: { value: MODE[transfer] }, uThr: { value: threshold }, uDensity: { value: density },
      uSteps: { value: Math.max(64, Math.min(320, src.grid[0] * 3)) },
    },
  }), [tex])

  useEffect(() => { loaded.current = [-1, -1] }, [src])
  useEffect(() => () => { tex[0].dispose(); tex[1].dispose(); material.dispose() }, [tex, material])

  const upload = (slot: 0 | 1, frame: number) => {
    const k = src.key(frame)
    if (loaded.current[slot] === k) return
    const d = src.data(frame)
    if (d.length !== (tex[slot].image.data as Uint8Array).length) return   // grid changed; new textures follow
    const t = tex[slot]
    ;(t.image.data as Uint8Array).set(d)
    t.needsUpdate = true
    loaded.current[slot] = k
  }

  useFrame(() => {
    if (!mesh.current || src.count < 1) return
    const n = src.count
    const pos = Math.min(Math.max(clock.current, 0), n - 1)
    const f0 = Math.floor(pos)
    const f1 = Math.min(f0 + 1, n - 1)
    upload(0, f0)
    upload(1, f1)
    const u = material.uniforms
    u.uMix.value = pos - f0
    u.uAffA.value.set(...src.affine(f0))
    u.uAffB.value.set(...src.affine(f1))
    u.uMode.value = MODE[transfer]
    u.uThr.value = threshold
    u.uDensity.value = density
    mesh.current.updateMatrixWorld()
    u.uCam.value.copy(camera.position).applyMatrix4(new THREE.Matrix4().copy(mesh.current.matrixWorld).invert())
  })

  return (
    <mesh ref={mesh} material={material}>
      <boxGeometry args={[1, 1, 1]} />
    </mesh>
  )
}
