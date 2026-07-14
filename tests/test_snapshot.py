"""tools/snapshot.py: dependency-free field->PNG screenshotter (supports the AGENTS.md reporting protocol).
Physics is never touched (visualisation only). Validates PNG output and recorded-lens decoding."""
import struct

import numpy as np

from tools import snapshot


def _png_dims(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"                 # valid PNG signature
    w, h = struct.unpack(">II", data[16:24])               # IHDR width/height
    return w, h


def test_render_field_writes_valid_png(tmp_path):
    field = np.add.outer(np.linspace(-1, 1, 32), np.linspace(-1, 1, 32))
    out = tmp_path / "f.png"
    snapshot.render_field(field, str(out), diverging=True, symmetric=True, px=320)
    w, h = _png_dims(str(out))
    assert w == h and w >= 320                              # upscaled square heatmap


def test_colormap_range_and_shape():
    x = np.linspace(0, 1, 50).reshape(5, 10)
    rgb = snapshot.colormap(x, diverging=False)
    assert rgb.shape == (5, 10, 3) and rgb.dtype == np.uint8
    assert rgb.min() >= 0 and rgb.max() <= 255


def test_decode_recorded_lens_matches_grid():
    """A recorded official-room lens decodes to (nframes, H, W) in physical units within [vmin, vmax]."""
    import json
    p = "app/public/data/rooms/room-g002-a/field.json"
    d = json.load(open(p))
    H, W = d["grid"]
    frames = snapshot.decode_lens(p, "temperature")
    assert frames.shape == (d["nframes"], H, W)
    L = d["lenses"]["temperature"]
    assert frames.min() >= L["vmin"] - 1e-6 and frames.max() <= L["vmax"] + 1e-6
