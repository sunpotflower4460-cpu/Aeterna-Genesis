/// <reference lib="webworker" />
// Off-main-thread: fetch a room's field.json + render-manifest, decode base64 uint8 -> Float32 norm
// per lens, and transfer the buffers back. Keeps the UI thread free while heavier recorded data loads.

interface Req { base: string; roomId: string }

self.onmessage = async (e: MessageEvent<Req>) => {
  const { base, roomId } = e.data
  try {
    const [fr, mr] = await Promise.all([
      fetch(base + 'rooms/' + roomId + '/field.json'),
      fetch(base + 'rooms/' + roomId + '/render-manifest.json'),
    ])
    const field: any = fr.ok ? await fr.json() : null
    const manifest: any = mr.ok ? await mr.json() : null
    if (!field) {
      ;(self as any).postMessage({ roomId, field: null, manifest, lenses: {} })
      return
    }
    const lenses: Record<string, any> = {}
    const transfers: ArrayBuffer[] = []
    for (const name of Object.keys(field.lenses)) {
      const L = field.lenses[name]
      const bin = atob(L.data_b64)
      const norm = new Float32Array(bin.length)
      for (let i = 0; i < bin.length; i++) norm[i] = bin.charCodeAt(i) / 255
      lenses[name] = {
        name, grid: field.grid, nframes: field.nframes, cyclic: L.cyclic,
        vmin: L.vmin, vmax: L.vmax, unit: L.unit, source: L.source, norm,
      }
      transfers.push(norm.buffer)
    }
    // drop the (now redundant) base64 payload before posting the field metadata back
    const meta = {
      ...field,
      lenses: Object.fromEntries(Object.keys(field.lenses).map((k) => {
        const { data_b64, ...rest } = field.lenses[k]
        return [k, rest]
      })),
    }
    ;(self as any).postMessage({ roomId, field: meta, manifest, lenses }, transfers)
  } catch (err) {
    ;(self as any).postMessage({ roomId, error: String(err) })
  }
}
