"""Statistics with the SERIES as the unit of replication (v0.1, PRE_REGISTRATION.json: statistics).

Generations within a series are not independent: every statistic is first reduced to one value per series, then
resampled over series. Generation-level pseudo-replication is refused by the function signatures (T20).
"""
import numpy as np


def series_values(array_sg):
    """Input must be one value per series: shape (n_series,). Anything else is refused."""
    v = np.asarray(array_sg, dtype=float)
    if v.ndim != 1:
        raise ValueError("statistics must be computed on one value per series (shape (n_series,))")
    return v


def bootstrap_ci(values, n_boot=10000, level=0.95, seed=0):
    """Percentile bootstrap over series. Returns (mean, lo, hi)."""
    v = series_values(values)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    means = v[idx].mean(axis=1)
    a = (1.0 - level) / 2.0
    return float(v.mean()), float(np.quantile(means, a)), float(np.quantile(means, 1.0 - a))


def bootstrap_ratio_ci(numer, denom, n_boot=10000, level=0.95, seed=0):
    """Ratio of means over paired series, percentile bootstrap over series. Returns (ratio, lo, hi)."""
    a_ = series_values(numer)
    b_ = series_values(denom)
    if a_.size != b_.size:
        raise ValueError("paired series required")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, a_.size, size=(n_boot, a_.size))
    ratios = a_[idx].mean(axis=1) / b_[idx].mean(axis=1)
    lo_q = (1.0 - level) / 2.0
    return float(a_.mean() / b_.mean()), float(np.quantile(ratios, lo_q)), float(np.quantile(ratios, 1.0 - lo_q))


def sign_flip_pvalue(values, n_perm=10000, seed=0):
    """Two-sided sign-flip permutation test of mean(values) = 0 over series (paired differences)."""
    v = series_values(values)
    obs = abs(v.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_perm, v.size))
    perm = np.abs((signs * v).mean(axis=1))
    return float((np.sum(perm >= obs) + 1) / (n_perm + 1))
