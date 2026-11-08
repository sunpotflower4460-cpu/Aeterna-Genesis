import * as THREE from 'three'

// Derived DISPLAY buffers. Source bytes are never mutated. Circle encoding makes phase interpolation
// periodic in space as well as time. Ambiguous averages are masked by decodeField in the shader.
const CIRCLE = Array.from({ length: 256 }, (_, i) => [
  Math.round((Math.cos(i / 255 * Math.PI * 2) * 0.5 + 0.5) * 255),
  Math.round((Math.sin(i / 255 * Math.PI * 2) * 0.5 + 0.5) * 255),
])
export function textureBytes(source: Uint8Array, cyclic: boolean): Uint8Array {
  if (!cyclic) return source.slice()
  const out = new Uint8Array(source.length * 2)
  for (let i = 0; i < source.length; i++) { out[i * 2] = CIRCLE[source[i]][0]; out[i * 2 + 1] = CIRCLE[source[i]][1] }
  return out
}
export function makeFieldTexture(grid: number[], cyclic: boolean): THREE.DataTexture | THREE.Data3DTexture {
  const data = new Uint8Array(grid.reduce((a, b) => a * b, 1) * (cyclic ? 2 : 1))
  const texture = grid.length === 3 ? new THREE.Data3DTexture(data, grid[2], grid[1], grid[0])
    : new THREE.DataTexture(data, grid[1], grid[0])
  texture.format = cyclic ? THREE.RGFormat : THREE.RedFormat
  texture.type = THREE.UnsignedByteType
  texture.minFilter = texture.magFilter = THREE.LinearFilter
  texture.unpackAlignment = 1
  texture.wrapS = texture.wrapT = THREE.ClampToEdgeWrapping
  if (texture instanceof THREE.Data3DTexture) texture.wrapR = THREE.ClampToEdgeWrapping
  return texture
}
export function uploadField(texture: THREE.DataTexture | THREE.Data3DTexture, source: Uint8Array, cyclic: boolean): boolean {
  const target = texture.image.data as Uint8Array
  if (target.length !== source.length * (cyclic ? 2 : 1)) return false
  target.set(cyclic ? textureBytes(source, true) : source)
  texture.needsUpdate = true
  return true
}
