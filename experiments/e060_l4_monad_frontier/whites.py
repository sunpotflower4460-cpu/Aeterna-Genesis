#!/usr/bin/env python3
"""e060 白の起動 — モナド前提を破らない初期条件。

前提（monad_audit.yaml）：白0は「これ以上分割できないもの」。個体は全体場の一つの
モードとして生まれねばならず、初期条件として切り出して置いてはならない（M3）。

したがって本モジュールの初期条件は **一様場＋ゼロ平均微小ノイズ** だけである。
置かないもの：ガウシアンbump／液滴／個体の中心座標／移動方向／境界や膜／分裂位置。

対照として従来の bump 入り IC も提供するが、それは Phase 0 の陽性対照専用であり、
`localization_seeded=True` を必ず伴う（正直な per-capability 記録・GPT②）。

no_touch: genesis/models/** と genesis/diagnostics/** は読むだけで書き換えない。
"""
from __future__ import annotations

import numpy as np

from genesis.models import ginzburg_landau as gl
from genesis.models import mass_conserved_3d as mc
from genesis.models import swift_hohenberg as sh


def zero_mean_noise(shape, rng):
    """厳密にゼロ平均へ射影したガウスノイズ。

    偶発的な大域オフセットも「置いた」ことになるため、平均を引いて射影する。
    これは対称性を壊す情報を一切与えないための操作であって、構造を与える操作ではない。
    """
    n = rng.standard_normal(shape)
    return n - n.mean()


def uniform_plus_noise(shape, mean_level, noise_amp, rng):
    """一様な平均値＋ゼロ平均ノイズのみ。局在も位置も方向も大きさも置かない。"""
    return float(mean_level) + float(noise_amp) * zero_mean_noise(shape, rng)


# --- mass_conserved（monadic: a+b が厳密保存） ---------------------------------

def mc_initial_uniform(shape, p, noise_amp, rng):
    """a は一様ゼロ近傍＋ゼロ平均ノイズ、b は一様 b0＋ゼロ平均ノイズ。

    bump を置かない。a+b の総和は b0*N（ノイズがゼロ平均なので厳密に保たれる）。
    """
    a = uniform_plus_noise(shape, 0.0, noise_amp, rng)
    b = uniform_plus_noise(shape, float(p["b0"]), noise_amp, rng)
    return a, b


def mc_initial_bump(shape, p, noise_amp, rng, bump_width=5.0, bump_amp=0.4):
    """Phase 0 陽性対照専用：従来どおり中心に対称bumpを置く（localization_seeded=True）。"""
    return mc.make_initial(shape, float(p["b0"]), rng, bump_width=bump_width,
                           bump_amp=bump_amp, noise_amp=noise_amp)


def mc_support_stats(a, thr):
    """a の閾値超え領域の (面積, 面積率, 連結成分数, 最大値, 重心)。

    連結成分数は G1「終盤の連結成分が1個」の直接の測定量。
    """
    from scipy import ndimage
    m = np.asarray(a) > float(thr)
    area = int(m.sum())
    amax = float(np.abs(a).max())
    if area == 0:
        return {"area": 0, "area_fraction": 0.0, "ncomp": 0, "amax": amax,
                "centroid": (float("nan"), float("nan"))}
    _, ncomp = ndimage.label(m)
    idx = np.indices(m.shape)
    cy = float((idx[0] * m).sum() / area)
    cx = float((idx[1] * m).sum() / area)
    return {"area": area, "area_fraction": area / float(m.size), "ncomp": int(ncomp),
            "amax": amax, "centroid": (cy, cx)}


# --- swift_hohenberg（monadic: 単一実スカラー） --------------------------------

def sh_initial_uniform(shape, p, noise_amp, rng):
    """u ~ 0 の一様背景＋ゼロ平均ノイズのみ。sh.make_initial の bump を使わない。"""
    return uniform_plus_noise(shape, 0.0, noise_amp, rng)


def sh_initial_bump(shape, p, noise_amp, rng):
    """Phase 0 陽性対照専用：従来の sh.make_initial（中心に1つのbump）。"""
    return sh.make_initial(shape, noise_amp, rng, p)


# --- 白ごとの一様IC起動テーブル ------------------------------------------------

WHITES = {
    "mass_conserved": {
        "module": mc,
        "monadicity": "monadic",
        "fields": ("a", "b"),
        "defaults": dict(mc.DEFAULTS),
    },
    "swift_hohenberg": {
        "module": sh,
        "monadicity": "monadic",
        "fields": ("u",),
        "defaults": dict(sh.DEFAULTS),
    },
    "g001_ginzburg_landau_quench": {
        "module": gl,
        "monadicity": "monadic",
        "fields": ("psi",),
        "defaults": dict(gl.DEFAULTS),
    },
}
