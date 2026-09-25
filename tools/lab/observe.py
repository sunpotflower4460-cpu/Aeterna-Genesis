"""Observation packet: one honest, provider-independent description of what happened in the tanks.

Every AI (and the person, in the "AI に渡したもの" tab) gets the SAME packet; models only differ in which
layers they can read:

1. 事件簿 (text + numbers) -- events detected MECHANICALLY from the measured time series and from blob
   tracking on the key frames: counts going up/down, jumps, settling, periods, blob motion / split / merge /
   birth / death. Every line names its rule and threshold, so a text-only model can "see" and anyone can
   check it.
2. Key frames -- PNGs (tools/snapshot.py, numpy + zlib), each paired with a caption in TEXT (time, lens,
   colour range, what bright means). 3D whites are shown as three projections side by side.
3. Motion -- a short sequence of small frames (and an mp4 when ffmpeg is installed) for models that read video.
4. Recipe, lineage and the white's measured ceiling (research/index.json).

Nothing here feeds back into a simulation, and nothing here decides what is emergent: the rules only
describe changes; interpretation is left to people and to the council, which must label visual impressions
as unmeasured.
"""
from __future__ import annotations

import base64
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage

from tools.lab import whites
from tools.snapshot import colormap, encode_png

_REPO = Path(__file__).resolve().parents[2]
COUNT_METRICS = {"spots", "defects", "peaks"}
MAX_LISTED_CHANGES = 12


# ============================================================================ time-series rules
def _series(samples: list[dict[str, Any]], key: str) -> tuple[np.ndarray, np.ndarray]:
    pts = [(s["t"], s["metrics"].get(key)) for s in samples]
    pts = [(t, v) for t, v in pts if isinstance(v, (int, float)) and v == v and math.isfinite(v)]
    if not pts:
        return np.zeros(0), np.zeros(0)
    t, v = np.array(pts, float).T
    return t, v


def _fmt(v: float) -> str:
    a = abs(v)
    if a >= 1000 or (a == int(a) and a < 1e6):
        return f"{v:.0f}" if a == int(a) else f"{v:.1f}"
    return f"{v:.3g}"


def count_changes(t: np.ndarray, v: np.ndarray, name: str) -> list[dict[str, Any]]:
    """Rule `count-change`: every change of an integer count between consecutive samples."""
    ev = []
    for i in range(1, len(v)):
        if v[i] != v[i - 1]:
            ev.append({"t": float(t[i]), "rule": "count-change", "metric": name, "before": float(v[i - 1]),
                       "after": float(v[i]),
                       "text": f"t={_fmt(t[i])}: {name} {_fmt(v[i - 1])} → {_fmt(v[i])}"})
    if len(ev) > MAX_LISTED_CHANGES:            # summarise: net change, direction counts, biggest steps
        ups = sum(e["after"] > e["before"] for e in ev)
        big = sorted(ev, key=lambda e: -abs(e["after"] - e["before"]))[:4]
        summary = {"t": float(t[-1]), "rule": "count-change-summary", "metric": name,
                   "before": float(v[0]), "after": float(v[-1]),
                   "text": (f"t={_fmt(t[0])}→{_fmt(t[-1])}: {name} {_fmt(v[0])} → {_fmt(v[-1])}"
                            f"（変化 {len(ev)} 回：増 {ups}・減 {len(ev) - ups}。大きい変化: "
                            + ", ".join(f"t={_fmt(e['t'])} {_fmt(e['before'])}→{_fmt(e['after'])}" for e in big) + "）")}
        return [summary]
    return ev


def jumps(t: np.ndarray, v: np.ndarray, name: str, k: float = 6.0, min_frac: float = 0.05) -> list[dict[str, Any]]:
    """Rule `jump(k=6,5%)`: a single step larger than k × the robust step scale (MAD) AND larger than 5% of the
    series' full range (so a converged, nearly constant series does not produce huge ratios)."""
    if len(v) < 8:
        return []
    d = np.diff(v)
    rng = float(v.max() - v.min())
    if rng <= 1e-3 * max(1.0, float(np.abs(v).mean())):   # effectively constant (e.g. a centroid that sits still)
        return []
    scale = max(float(np.median(np.abs(d - np.median(d)))) * 1.4826, 1e-3 * rng)
    out = []
    for i in np.nonzero((np.abs(d) > k * scale) & (np.abs(d) > min_frac * rng))[0][:5]:
        out.append({"t": float(t[i + 1]), "rule": f"jump(k={k:g},{min_frac:.0%})", "metric": name,
                    "before": float(v[i]), "after": float(v[i + 1]),
                    "text": f"t={_fmt(t[i + 1])}: {name} が 1 コマで大きく変化 {_fmt(v[i])} → {_fmt(v[i + 1])}"
                            f"（全体の幅の {abs(d[i]) / rng:.0%}）"})
    return out


def settled(t: np.ndarray, v: np.ndarray, name: str, frac: float = 0.2, tol: float = 0.01) -> dict[str, Any] | None:
    """Rule `settled(last 20%, 1%)`: over the last 20% of the record the value moved < 1% of its full range."""
    if len(v) < 10:
        return None
    rng = float(v.max() - v.min())
    tail = v[int(len(v) * (1 - frac)):]
    if rng > 0 and float(tail.max() - tail.min()) < tol * rng:
        return {"t": float(t[-1]), "rule": "settled(last 20%,1%)", "metric": name, "value": float(tail[-1]),
                "text": f"{name} は最後の 20% でほぼ一定（{_fmt(tail[-1])}・全体の幅の 1% 未満の動き）"}
    return None


def period(t: np.ndarray, v: np.ndarray, name: str, min_acf: float = 0.5) -> dict[str, Any] | None:
    """Rule `period(acf>0.5)`: first autocorrelation peak of the detrended series on a uniform time grid."""
    if len(v) < 24 or t[-1] <= t[0]:
        return None
    n = min(len(v), 512)
    tu = np.linspace(t[0], t[-1], n)
    vu = np.interp(tu, t, v)
    vu = vu - np.polyval(np.polyfit(tu, vu, 1), tu)
    if not np.any(vu):
        return None
    ac = np.correlate(vu, vu, "full")[n - 1:]
    ac = ac / ac[0]
    for i in range(2, n // 2):
        if ac[i] > ac[i - 1] and ac[i] >= ac[i + 1] and ac[i] > min_acf:
            p = float(tu[i] - tu[0])
            cycles = (t[-1] - t[0]) / p
            if cycles >= 3:
                return {"t": float(t[-1]), "rule": f"period(acf>{min_acf:g})", "metric": name, "period": p,
                        "acf": float(ac[i]),
                        "text": f"{name} が周期 ≈ {_fmt(p)}（時間の単位）で振動（自己相関 {ac[i]:.2f}・{cycles:.0f} 周期分）"}
            return None
    return None


def timeline(samples: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]:
    keys: list[str] = []
    for s in samples:
        for k in s["metrics"]:
            if k not in keys:
                keys.append(k)
    events: list[dict[str, Any]] = []
    summary: dict[str, dict[str, float]] = {}
    for k in keys:
        t, v = _series(samples, k)
        if not len(v):
            continue
        summary[k] = {"first": float(v[0]), "last": float(v[-1]), "min": float(v.min()), "max": float(v.max()),
                      "t0": float(t[0]), "t1": float(t[-1]), "n": int(len(v))}
        if k in COUNT_METRICS:
            events += count_changes(t, v, k)
        else:
            events += jumps(t, v, k)
        for rule in (settled, period):
            e = rule(t, v, k)
            if e:
                events.append(e)
    events.sort(key=lambda e: e["t"])
    return events, summary


# ============================================================================ blob tracking (2D)
def _decode(lens: dict[str, Any]) -> np.ndarray:
    q = np.frombuffer(lens["data"], np.uint8).reshape(lens["grid"]).astype(float)
    return lens["lo"] + q / 255.0 * ((lens["hi"] - lens["lo"]) or 1.0)


def periodic_blobs(mask: np.ndarray, min_size: int = 3) -> list[dict[str, float]]:
    """Connected blobs on a periodic 2D grid: labels touching across an edge are merged; centroids are
    circular means per axis. Returns [{y, x, area}]."""
    lbl, n = ndimage.label(mask)
    if n == 0:
        return []
    parent = list(range(n + 1))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in ((lbl[0, :], lbl[-1, :]), (lbl[:, 0], lbl[:, -1])):
        for i, j in zip(a, b):
            if i and j:
                parent[find(i)] = find(j)
    roots = np.array([find(i) for i in range(n + 1)])
    lbl = roots[lbl]
    H, W = mask.shape
    ys, xs = np.nonzero(lbl)
    out = []
    for r in np.unique(lbl[ys, xs]):
        sel = lbl[ys, xs] == r
        if sel.sum() < min_size:
            continue
        ang_y, ang_x = 2 * np.pi * ys[sel] / H, 2 * np.pi * xs[sel] / W
        cy = (np.arctan2(np.sin(ang_y).mean(), np.cos(ang_y).mean()) % (2 * np.pi)) * H / (2 * np.pi)
        cx = (np.arctan2(np.sin(ang_x).mean(), np.cos(ang_x).mean()) % (2 * np.pi)) * W / (2 * np.pi)
        out.append({"y": float(cy), "x": float(cx), "area": float(sel.sum())})
    return out


def _pdist(a: dict[str, float], b: dict[str, float], shape: tuple[int, int]) -> float:
    dy = abs(a["y"] - b["y"])
    dx = abs(a["x"] - b["x"])
    return math.hypot(min(dy, shape[0] - dy), min(dx, shape[1] - dx))


def track(keyframes: list[dict[str, Any]], spec: tuple[str, float, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Rule `track(nearest, r)`: blobs above/below a threshold in consecutive key frames are matched to the
    nearest blob within r = max(4, 1.5·sqrt(area/π)+2) cells. One→two = split, two→one = merge, unmatched
    new = birth, unmatched old = death. Returns (events, per-frame blob lists)."""
    lens, thr, side = spec
    frames = []
    for k in keyframes:
        if lens not in k["lenses"]:
            continue
        a = _decode(k["lenses"][lens])
        frames.append((k, periodic_blobs(a > thr if side == "above" else a < thr)))
    events: list[dict[str, Any]] = []
    moves: list[tuple[float, float, float]] = []
    for (k0, b0), (k1, b1) in zip(frames, frames[1:]):
        shape = tuple(k1["lenses"][lens]["grid"])
        fwd: dict[int, list[int]] = {i: [] for i in range(len(b0))}
        back: dict[int, list[int]] = {j: [] for j in range(len(b1))}
        for j, q in enumerate(b1):
            if not b0:
                break
            d = [_pdist(p, q, shape) for p in b0]
            i = int(np.argmin(d))
            r = max(4.0, 1.5 * math.sqrt(b0[i]["area"] / math.pi) + 2)
            if d[i] <= r:
                fwd[i].append(j)
                back[j].append(i)
        for i, p in enumerate(b0):             # two old blobs whose nearest new blob is the same one -> merge
            if not b1:
                break
            d = [_pdist(p, q, shape) for q in b1]
            j = int(np.argmin(d))
            if d[j] <= max(4.0, 1.5 * math.sqrt(p["area"] / math.pi) + 2) and i not in back[j]:
                back[j].append(i)
        t0, t1 = k0["t"], k1["t"]
        span = f"t={_fmt(t0)}→{_fmt(t1)}"
        for i, js in fwd.items():
            if len(js) >= 2:
                events.append({"t": t1, "rule": "track:split", "text": f"{span}: 塊が分裂（({_fmt(b0[i]['x'])},{_fmt(b0[i]['y'])}) → {len(js)} 個）"})
        births = [j for j, is_ in back.items() if not is_]
        deaths = [i for i, js in fwd.items() if not js and not any(i in v for v in back.values())]
        for j, is_ in back.items():
            if len(is_) >= 2:
                events.append({"t": t1, "rule": "track:merge", "text": f"{span}: {len(is_)} 個の塊が合体（→ ({_fmt(b1[j]['x'])},{_fmt(b1[j]['y'])})）"})
        for kind, idx, blobs, word in (("birth", births, b1, "新しい塊"), ("death", deaths, b0, "塊が消滅")):
            if not idx:
                continue
            where = ", ".join(f"({_fmt(blobs[i]['x'])},{_fmt(blobs[i]['y'])})" for i in idx[:4]) + (" …" if len(idx) > 4 else "")
            events.append({"t": t1, "rule": f"track:{kind}", "count": len(idx),
                           "text": f"{span}: {word} {len(idx)} 個 {where}"})
        if t1 > t0:                              # one-to-one matches: displacement per time unit
            for i, js in fwd.items():
                if len(js) == 1 and len(back[js[0]]) == 1:
                    moves.append((_pdist(b0[i], b1[js[0]], shape), t1 - t0, t1))
    if moves:
        speeds = np.array([d / dt for d, dt, _ in moves])
        disp = np.array([d for d, _, _ in moves])
        imax = int(np.argmax(speeds))
        events.append({"t": frames[-1][0]["t"], "rule": "track:motion-summary", "max_speed": float(speeds.max()),
                       "median_speed": float(np.median(speeds)),
                       "text": (f"塊の移動（1 対 1 で対応できた {len(moves)} 組）：キーフレーム間の変位 中央値 {_fmt(float(np.median(disp)))} マス・"
                                f"最大 {_fmt(float(disp.max()))} マス／速さ 中央値 {float(np.median(speeds)):.3g}・最大 {speeds[imax]:.3g} マス/時間"
                                f"（t≈{_fmt(moves[imax][2])}）。1 マス前後の変位は形の変化や量子化でも起こる")})
    counts = [{"t": k["t"], "n": len(b)} for k, b in frames]
    return events, counts


# ============================================================================ images
def _hue(x01: np.ndarray) -> np.ndarray:
    h = (x01 % 1.0) * 6.0
    c = np.ones_like(h) * 0.85
    xx = c * (1 - np.abs(h % 2 - 1))
    z = np.zeros_like(h)
    conds = [(h < 1), (h < 2), (h < 3), (h < 4), (h < 5), (h >= 5)]
    rgbs = [(c, xx, z), (xx, c, z), (z, c, xx), (z, xx, c), (xx, z, c), (c, z, xx)]
    out = np.zeros(h.shape + (3,))
    done = np.zeros(h.shape, bool)
    for cond, (r, g, b) in zip(conds, rgbs):
        m = cond & ~done
        out[m] = np.stack([r[m], g[m], b[m]], -1)
        done |= m
    return ((out + 0.1) / 0.95 * 255).clip(0, 255).astype(np.uint8)


def _rgb(a01: np.ndarray, transfer: str) -> np.ndarray:
    if transfer == "cyclic":
        return _hue(a01)
    if transfer == "low":
        return colormap(1.0 - a01)
    return colormap(a01, diverging=(transfer == "diverging"))


def _up(rgb: np.ndarray, px: int) -> np.ndarray:
    r = max(1, px // max(rgb.shape[:2]))
    return np.kron(rgb, np.ones((r, r, 1), np.uint8))


def frame_image(lens_frame: dict[str, Any], spec: whites.Lens, px: int = 288) -> tuple[bytes, str]:
    """PNG + the text that must accompany it. 2D: the field. 3D: three projections (x, y, z) side by side --
    min for 'low' lenses (cores), max otherwise, a middle slice for cyclic phase."""
    a = _decode(lens_frame)
    lo, hi = (spec.vmin, spec.vmax) if spec.cyclic else (lens_frame["lo"], lens_frame["hi"])
    if spec.transfer == "diverging":             # white must mean 0, not the middle of this frame's range
        m = max(abs(lo), abs(hi))
        lo, hi = -m, m
    n01 = lambda x: np.clip((x - lo) / ((hi - lo) or 1.0), 0, 1)  # noqa: E731
    if a.ndim == 2:
        rgb = _up(_rgb(n01(a), spec.transfer), px)
        how = "2D の場そのもの"
    else:
        if spec.cyclic:
            views = [a[a.shape[0] // 2], a[:, a.shape[1] // 2], a[:, :, a.shape[2] // 2]]
            how = "3D の中央断面 3 枚（左から 軸0・軸1・軸2 に垂直）"
        else:
            f = np.min if spec.transfer == "low" else np.max
            views = [f(a, axis=ax) for ax in range(3)]
            how = f"3D の{'最小' if spec.transfer == 'low' else '最大'}値投影 3 枚（左から 軸0・軸1・軸2 方向に投影）"
        tiles = [_up(_rgb(n01(v), spec.transfer), px // 2) for v in views]
        gap = np.full((tiles[0].shape[0], 4, 3), 20, np.uint8)
        rgb = np.concatenate([tiles[0], gap, tiles[1], gap, tiles[2]], axis=1)
    bright = {"high": "明るい＝値が大きい", "low": "明るい＝値が小さい（芯・穴）", "cyclic": "色相＝位相（-π..π を一周）",
              "diverging": "青＝小さい・白＝中間・赤＝大きい"}[spec.transfer]
    caption = f"レンズ {spec.name}（{spec.label}）・{how}・色の範囲 {_fmt(lo)}〜{_fmt(hi)}・{bright}"
    return encode_png(rgb), caption


def diff_image(a_frame: dict[str, Any], b_frame: dict[str, Any], px: int = 288) -> tuple[bytes, str] | None:
    a, b = _decode(a_frame), _decode(b_frame)
    if a.shape != b.shape:
        return None
    d = b - a
    if d.ndim == 3:
        d = d.max(axis=0) + d.min(axis=0)
    m = float(np.abs(d).max()) or 1.0
    rgb = _up(colormap((d / m + 1) / 2, diverging=True), px)
    return encode_png(rgb), f"差分（後 − 前）・赤＝増えた・青＝減った・白＝変化なし・最大の変化 {_fmt(m)}"


def video_mp4(frames: list[np.ndarray], fps: int = 6) -> bytes | None:
    """mp4 via ffmpeg when installed (for models that read video); None otherwise."""
    exe = shutil.which("ffmpeg")
    if not exe or not frames:
        return None
    h, w = frames[0].shape[:2]
    h2, w2 = h - h % 2, w - w % 2
    raw = b"".join(np.ascontiguousarray(f[:h2, :w2]).tobytes() for f in frames)
    try:
        p = subprocess.run([exe, "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w2}x{h2}",
                            "-r", str(fps), "-i", "-", "-pix_fmt", "yuv420p", "-movflags", "frag_keyframe+empty_moov",
                            "-f", "mp4", "-"], input=raw, capture_output=True, timeout=60)
        return p.stdout if p.returncode == 0 and p.stdout else None
    except (OSError, subprocess.SubprocessError):
        return None


# ============================================================================ packet
def _ceiling(white: whites.White) -> dict[str, Any] | None:
    if not white.ceiling_ref:
        return None
    try:
        idx = json.loads((_REPO / "research" / "index.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for w in idx.get("whites", []):
        if w.get("id") == white.ceiling_ref:
            return {k: w.get(k) for k in ("id", "name", "reached", "tier", "ceiling_reason")}
    return None


def _pick(keyframes: list[dict[str, Any]], n: int = 7) -> list[dict[str, Any]]:
    """Evenly spaced key frames plus every tagged (before/after intervention) one, in time order."""
    if not keyframes:
        return []
    idx = set(np.linspace(0, len(keyframes) - 1, min(n, len(keyframes))).round().astype(int).tolist())
    idx |= {i for i, k in enumerate(keyframes) if k["tag"]}
    chosen = [keyframes[i] for i in sorted(idx)]
    if len(chosen) > 12:
        tagged = [k for k in chosen if k["tag"]][-6:]
        rest = [k for k in chosen if not k["tag"]]
        rest = [rest[i] for i in np.linspace(0, len(rest) - 1, 12 - len(tagged)).round().astype(int)] if rest else []
        chosen = sorted({id(k): k for k in tagged + rest}.values(), key=lambda k: k["seq"])
    return chosen


def describe_recipe(white: whites.White, info: dict[str, Any]) -> list[str]:
    r = info["recipe"]
    lines = [f"白: {white.title}（{white.family}・{white.dimension}D・格子 {'×'.join(map(str, white.grid))}・モデル {white.model}）",
             f"t=0 に置いたもの: {' / '.join(white.put_in)}（seed {r['seed']}）"]
    changed = {k: v for k, v in r["knobs"].items() if white.knob(k).default != v}
    if changed:
        lines.append("t=0 のつまみ（既定から変えたもの）: " + ", ".join(f"{white.knob(k).label} {k}={v}" for k, v in changed.items()))
    dt = float(white.defaults.get("dt", 1.0))
    fork = info.get("fork_index")
    for i, ev in enumerate(r["events"]):
        who = "分岐で加えた" if fork is not None and i >= fork else ("親から受け継いだ" if fork is not None else "加えた")
        if ev["kind"] == "set":
            what = ", ".join(f"{white.knob(k).label} {k}={v}" for k, v in ev["values"].items())
        else:
            what = f"摂動 {white.perturb_spec(ev['name']).label} {ev.get('args') or ''}"
        lines.append(f"t={_fmt(ev['step'] * dt)}（{who}）: {what}")
    return lines


def build(hub, ids: list[str], motion_frames: int = 16) -> dict[str, Any]:
    """Assemble the packet for the given universes (read-only w.r.t. the simulations)."""
    universes = []
    for uid in ids:
        info = hub.info(uid)
        white = whites.get(info["white"])
        samples, keyframes = hub.observation(uid)
        events, summary = timeline(samples)
        dt = float(white.defaults.get("dt", 1.0))
        fork = info.get("fork_index")
        for i, ev in enumerate(info["recipe"]["events"]):
            if ev["kind"] == "set":
                what = "場の法則を変更 " + ", ".join(f"{k}={v}" for k, v in ev["values"].items())
            else:
                what = f"摂動 {white.perturb_spec(ev['name']).label} {ev.get('args') or ''}"
            who = "分岐で" if fork is not None and i >= fork else "人が"
            events.append({"t": ev["step"] * dt, "rule": "置いた（介入）", "text": f"t={_fmt(ev['step'] * dt)}: {who}{what}"})
        events.sort(key=lambda e: e["t"])
        counts: list[dict[str, Any]] = []
        if white.track and white.dimension == 2:
            tev, counts = track(keyframes, white.track)
            events = sorted(events + tev, key=lambda e: e["t"])
        lens_name = white.track[0] if white.track else white.lenses[0].name
        spec = next(L for L in white.lenses if L.name == lens_name)
        images = []
        for k in _pick(keyframes):
            if lens_name not in k["lenses"]:
                continue
            png, cap = frame_image(k["lenses"][lens_name], spec)
            tag = f"・{k['tag']}" if k["tag"] else ""
            images.append({"kind": "keyframe", "t": k["t"], "step": k["step"], "png": png,
                           "caption": f"宇宙 {info['label']}・t={_fmt(k['t'])}（step {k['step']}{tag}）・{cap}"})
        if len(keyframes) >= 2 and lens_name in keyframes[0]["lenses"] and lens_name in keyframes[-1]["lenses"]:
            before = next((k for k in reversed(keyframes) if (k["tag"] or "").startswith("before")), keyframes[0])
            after = keyframes[-1]
            d = diff_image(before["lenses"][lens_name], after["lenses"][lens_name])
            if d:
                images.append({"kind": "diff", "t": after["t"], "step": after["step"], "png": d[0],
                               "caption": f"宇宙 {info['label']}・t={_fmt(before['t'])} → t={_fmt(after['t'])} の{d[1]}"})
        seq_src = keyframes[-motion_frames:]
        seq = []
        for k in seq_src:
            if lens_name in k["lenses"]:
                a = _decode(k["lenses"][lens_name])
                lo, hi = spec.vmin, spec.vmax
                if a.ndim == 3:
                    a = (np.min if spec.transfer == "low" else np.max)(a, axis=0)
                seq.append(_up(_rgb(np.clip((a - lo) / ((hi - lo) or 1), 0, 1), spec.transfer), 192))
        universes.append({
            "id": uid, "label": info["label"], "white": white.id, "title": white.title, "dimension": white.dimension,
            "step": info["step"], "t": info["t"], "parent": info["parent"], "branch_step": info["branch_step"],
            "recipe": info["recipe"], "recipe_text": describe_recipe(white, info), "ceiling": _ceiling(white),
            "source": white.source, "events": events, "summary": summary, "blob_counts": counts,
            "images": images,
            "motion": {"t": [k["t"] for k in seq_src if lens_name in k["lenses"]],
                       "frames": [encode_png(f) for f in seq],
                       "caption": (f"宇宙 {info['label']} の動き：キーフレーム {len(seq)} 枚を時間順に（固定の色範囲 "
                                   f"{_fmt(spec.vmin)}〜{_fmt(spec.vmax)}{'・3D は軸0 方向の投影' if white.dimension == 3 else ''}）"),
                       "mp4": video_mp4(seq)},
        })
    return {"version": 1, "universes": universes, "text": to_text(universes)}


def to_text(universes: list[dict[str, Any]]) -> str:
    """The 事件簿 as plain text: what a text-only model reads (and what every model reads first)."""
    out = ["# 観測パケット（測定から機械的に作った事件簿）",
           "規則の名前と閾値を各行に付けた。解釈はしていない。画像の見た目の印象は『見た目（未測定）』として区別すること。"]
    for u in universes:
        out.append(f"\n## 宇宙 {u['label']}（{u['id']}）: {u['title']} — いま t={_fmt(u['t'])}・step {u['step']}")
        out += [f"- {line}" for line in u["recipe_text"]]
        if u["parent"]:
            out.append(f"- 分岐元: {u['parent']}（step {u['branch_step']} で分かれた）")
        c = u["ceiling"]
        out.append(f"- この白の測定済みの天井: {c['reached']}（{c['tier']}）— {c['ceiling_reason']}" if c
                   else f"- この白の天井: research/index.json に項目なし（出典 {u['source']}）")
        if u["summary"]:
            out.append("### 測定値の要約（この画面で記録した範囲）")
            for k, s in u["summary"].items():
                out.append(f"- {k}: 最初 {_fmt(s['first'])} → 最後 {_fmt(s['last'])}（最小 {_fmt(s['min'])}・最大 {_fmt(s['max'])}・"
                           f"t={_fmt(s['t0'])}〜{_fmt(s['t1'])}・{s['n']} 点）")
        out.append("### 出来事（時間順）")
        # interventions and whole-record rules always; per-interval tracking lines fill up to 40 (newest first kept)
        ev = u["events"]
        keep = {id(e) for e in ev if not e["rule"].startswith("track:") or e["rule"] == "track:motion-summary"}
        room = max(0, 40 - len(keep))
        keep |= {id(e) for e in [e for e in ev if id(e) not in keep][-room:]} if room else set()
        shown = [e for e in ev if id(e) in keep]
        out += [f"- [{e['rule']}] {e['text']}" for e in shown] or ["- （規則にかかる出来事はなかった）"]
        if len(shown) < len(ev):
            out.append(f"- …ほか 追跡の行 {len(ev) - len(shown)} 件を省略（古いもの）")
        out.append(f"### 画像 {len(u['images'])} 枚・動き {len(u['motion']['frames'])} コマ（各画像の説明は画像の直前に付ける）")
    return "\n".join(out)


def to_public(packet: dict[str, Any]) -> dict[str, Any]:
    """JSON for the browser tab 'AI に渡したもの' (images as data URLs)."""
    b64 = lambda b: "data:image/png;base64," + base64.b64encode(b).decode("ascii")  # noqa: E731
    us = []
    for u in packet["universes"]:
        us.append({**{k: v for k, v in u.items() if k not in ("images", "motion")},
                   "images": [{**{k: v for k, v in im.items() if k != "png"}, "src": b64(im["png"])} for im in u["images"]],
                   "motion": {"t": u["motion"]["t"], "caption": u["motion"]["caption"],
                              "frames": [b64(f) for f in u["motion"]["frames"]], "has_mp4": u["motion"]["mp4"] is not None}})
    return {"version": packet["version"], "text": packet["text"], "universes": us}


def save(packet: dict[str, Any], directory: Path) -> Path:
    """Write the packet as the council saw it: packet.md, packet.json (no pixels) and the PNGs."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "packet.md").write_text(packet["text"], encoding="utf-8")
    meta = []
    for u in packet["universes"]:
        files = []
        for i, im in enumerate(u["images"]):
            name = f"{u['label']}_{i:02d}_{im['kind']}.png"
            (directory / name).write_bytes(im["png"])
            files.append({"file": name, "caption": im["caption"]})
        if u["motion"]["mp4"]:
            (directory / f"{u['label']}_motion.mp4").write_bytes(u["motion"]["mp4"])
        meta.append({**{k: v for k, v in u.items() if k not in ("images", "motion")}, "images": files,
                     "motion_frames": len(u["motion"]["frames"])})
    (directory / "packet.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    return directory


def main(argv: list[str] | None = None) -> int:
    """Build a packet without the lab server (e.g. for Claude Code): run one white from t=0 in-process."""
    import argparse
    from tools.lab.hub import LocalHub
    ap = argparse.ArgumentParser(description="observation packet for one white run from t=0 (no server)")
    ap.add_argument("--white", required=True, choices=sorted(whites.registry()))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--frames", type=int, default=40, help="frames to run (each = steps_per_frame steps)")
    ap.add_argument("--set", action="append", default=[], metavar="KNOB=VALUE", help="t=0 knob (repeatable)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    knobs = {k: float(v) for k, v in (x.split("=", 1) for x in a.set)}
    hub = LocalHub()
    uid = hub.create(a.white, a.seed, knobs)
    hub.run(uid, a.frames)
    d = save(build(hub, [uid]), a.out)
    print(f"{d}/packet.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
