#!/usr/bin/env python3
"""FieldRecorder — write compact, honest, replayable field snapshots for the Observatory (Phase 0).

For each run we keep only what the simulation ALREADY computed: at ~a dozen evenly spaced times we take
the real-space lens fields (e.g. temperature, |velocity|, vorticity), DOWNSAMPLE them for display, and
QUANTIZE to uint8 with the stored [vmin, vmax] so the browser can reconstruct value = vmin + u8/255 *
(vmax - vmin). The result is one `field.json` per run (referenced from the room, NOT inlined into
catalog.json) plus a machine-readable `render-manifest.yaml` mapping every lens to its measured field
with honesty flags (interpolated_for_display, changes_physics=false, decorative_particles=false).

This module is read-only w.r.t. the simulation: recording a run must leave its numerics — and its
final-field checksum — bit-identical.
"""

import base64
import json
import os

import numpy as np
from scipy import ndimage

SCHEMA_VERSION = 1


def downsample(arr, target):
    """Linear-interpolation resize to `target` grid (honest: interpolated_for_display). 2D or 3D."""
    arr = np.asarray(arr, dtype=float)
    target = tuple(int(t) for t in target)
    if arr.shape == target:
        return arr
    zoom = [t / s for t, s in zip(target, arr.shape)]
    out = ndimage.zoom(arr, zoom, order=1, mode="nearest")
    # enforce EXACT target shape (zoom can round to +/-1)
    for ax, t in enumerate(target):
        if out.shape[ax] > t:
            out = np.take(out, range(t), axis=ax)
        elif out.shape[ax] < t:
            pad = [(0, 0)] * out.ndim
            pad[ax] = (0, t - out.shape[ax])
            out = np.pad(out, pad, mode="edge")
    return out


class FieldRecorder:
    """Accumulate downsampled lens fields over time, then emit field.json + render-manifest."""

    def __init__(self, dimension, target):
        assert dimension in (2, 3)
        self.dim = dimension
        self.target = tuple(int(t) for t in target)
        self.times = []
        self.frames = {}   # lens -> list of downsampled arrays
        self.meta = {}     # lens -> {source, unit, transform, cyclic, geometry}

    def declare(self, lens, source, unit, transform="linear", cyclic=False, geometry=None):
        self.meta[lens] = {"source": source, "unit": unit, "transform": transform,
                           "cyclic": bool(cyclic),
                           "geometry": geometry or ("volume" if self.dim == 3 else "plane")}
        self.frames[lens] = []
        return self

    def add(self, t, fields):
        """Record one snapshot. `fields` maps declared lens -> full-resolution real-space array."""
        self.times.append(float(t))
        for lens in self.meta:
            self.frames[lens].append(downsample(fields[lens], self.target))

    def _quantize(self, lens):
        m = self.meta[lens]
        stack = np.stack(self.frames[lens], axis=0)          # (nframes, *target)
        if m["cyclic"]:
            vmin, vmax = -np.pi, np.pi
        else:
            vmin, vmax = float(np.min(stack)), float(np.max(stack))
        span = (vmax - vmin) or 1.0
        q = np.clip(np.round((stack - vmin) / span * 255.0), 0, 255).astype(np.uint8)
        return {"source": m["source"], "unit": m["unit"], "transform": m["transform"],
                "cyclic": m["cyclic"], "geometry": m["geometry"],
                "vmin": round(vmin, 6), "vmax": round(vmax, 6), "quant": "uint8",
                "data_b64": base64.b64encode(np.ascontiguousarray(q).tobytes()).decode("ascii")}

    def field_doc(self):
        return {"schema_version": SCHEMA_VERSION, "dimension": self.dim, "grid": list(self.target),
                "nframes": len(self.times), "times": [round(t, 4) for t in self.times],
                "downsample": "scipy.ndimage.zoom(order=1)",
                "lenses": {lens: self._quantize(lens) for lens in self.meta},
                "honesty": {"decorative_particles": False, "interpolated_for_display": True,
                            "changes_physics": False, "quantized_uint8": True}}

    def render_manifest(self, room_id, frames_ref):
        lenses = []
        for lens, m in self.meta.items():
            lenses.append({
                "lens": lens, "source": {"field": m["source"], "unit": m["unit"]},
                "mapping": {"transform": m["transform"], "cyclic": m["cyclic"], "clipping": "none"},
                "geometry": m["geometry"],
                "honesty": {"decorative_particles": False, "interpolated_for_display": True,
                            "changes_physics": False}})
        return {"room_id": room_id, "frames_ref": frames_ref, "dimension": self.dim,
                "lenses": lenses, "data_source": "physics", "separated_from_physics_data": True}

    def write_field(self, out_dir, name="field.json"):
        os.makedirs(out_dir, exist_ok=True)
        doc = self.field_doc()
        with open(os.path.join(out_dir, name), "w") as f:
            json.dump(doc, f, separators=(",", ":"))
        return doc

    # --- helper for readers/tests: reconstruct a lens' frames as float arrays ---
    @staticmethod
    def decode_lens(field_doc, lens):
        L = field_doc["lenses"][lens]
        raw = np.frombuffer(base64.b64decode(L["data_b64"]), dtype=np.uint8)
        grid = tuple(field_doc["grid"])
        arr = raw.reshape((field_doc["nframes"],) + grid).astype(float)
        return L["vmin"] + arr / 255.0 * ((L["vmax"] - L["vmin"]) or 1.0)


def snapshot_scheduler(t_end, n_frames):
    """Return evenly spaced target times in (0, t_end]; a run records when it first crosses each."""
    return [t_end * (i + 1) / n_frames for i in range(n_frames)]
