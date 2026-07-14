#!/usr/bin/env python3
"""Dependency-free field -> PNG screenshotter (numpy + zlib only; no matplotlib/Pillow needed).

Lets a human SEE any run: render a 2D physical field to a colour heatmap, or decode a recorded render
`field.json` lens (the same data the Observatory App shows). Visualisation NEVER touches physics
(`render.yaml` separated_from_physics_data / honesty block). Used by the AGENTS.md reporting protocol
("📸 スクリーンショット every time"). no_touch-safe: reads fields, writes PNGs; does not modify measures.py.

CLI:
    python tools/snapshot.py room room-g002-a temperature out.png       # recorded lens (last frame)
"""
import base64
import json
import struct
import sys
import zlib

import numpy as np

# perceptually-ordered anchors (viridis-ish sequential; blue-white-red diverging)
_VIRIDIS = np.array([[68, 1, 84], [59, 82, 139], [33, 145, 140], [94, 201, 98], [253, 231, 37]], float)
_DIVERG = np.array([[33, 102, 172], [103, 169, 207], [247, 247, 247], [239, 138, 98], [178, 24, 43]], float)


def write_png(rgb, path):
    """Write an (H, W, 3) uint8 array to a PNG file (pure zlib/struct, no image libs)."""
    rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
    H, W, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(H))

    def _chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(_chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)))
        f.write(_chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(_chunk(b"IEND", b""))
    return path


def colormap(x01, diverging=False):
    """Map a [0,1] array to (…, 3) uint8 RGB by interpolating perceptual anchors."""
    anchors = _DIVERG if diverging else _VIRIDIS
    x = np.clip(x01, 0.0, 1.0) * (len(anchors) - 1)
    lo = np.floor(x).astype(int)
    hi = np.minimum(lo + 1, len(anchors) - 1)
    f = (x - lo)[..., None]
    return (anchors[lo] * (1.0 - f) + anchors[hi] * f).astype(np.uint8)


def _upscale(a, px=360):
    r = max(1, px // a.shape[0])
    return np.kron(a, np.ones((r, r), a.dtype))


def render_field(field2d, path, diverging=False, symmetric=False, px=360):
    """Render a 2D field to a heatmap PNG. symmetric=True centres the colour scale at 0 (for ± fields)."""
    a = np.asarray(field2d, float)
    if symmetric:
        m = float(np.abs(a).max()) + 1e-12
        n = (a / m + 1.0) / 2.0
    else:
        lo, hi = float(a.min()), float(a.max())
        n = (a - lo) / (hi - lo + 1e-12)
    return write_png(colormap(_upscale(n, px), diverging=diverging), path)


def decode_lens(field_json_path, lens):
    """Decode a recorded render `field.json` lens to a (nframes, H, W) float array in physical units."""
    d = json.load(open(field_json_path))
    H, W = d["grid"]
    nf = d["nframes"]
    L = d["lenses"][lens]
    arr = np.frombuffer(base64.b64decode(L["data_b64"]), np.uint8).reshape(nf, H, W).astype(float)
    return L["vmin"] + (L["vmax"] - L["vmin"]) * arr / 255.0


def render_room_lens(room_id, lens, path, frame=-1, base="app/public/data/rooms"):
    """Render one recorded lens frame of an official room (as the Observatory App shows it)."""
    field = decode_lens(f"{base}/{room_id}/field.json", lens)[frame]
    return render_field(field, path, diverging=True, symmetric=True)


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "room":
        _, _, room_id, lens, out = sys.argv[:5]
        print(render_room_lens(room_id, lens, out))
    else:
        print(__doc__)
        sys.exit(1)
