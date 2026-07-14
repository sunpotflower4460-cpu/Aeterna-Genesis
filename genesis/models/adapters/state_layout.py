#!/usr/bin/env python3
"""Frontier Campaign M2 -- StateLayout: bundle all fields of a (possibly multi-field) white into ONE state
vector so the COUPLED Jacobian can be linearised (docs/ANGULAR_MODES.md M2). A single-field white is the
trivial case; a two/three-field white bundles (u, v[, w]).

Per the GPT M2 addendum §4: overlaps/projections use a per-field-weighted inner product (`state_metric`)
when fields differ greatly in magnitude -- but the eigenvalues themselves must not depend on the weights
(that is a test, tests/test_coupled_spectrum.py).
"""

import numpy as np


class StateLayout:
    def __init__(self, names, shapes, metric=None):
        self.names = tuple(names)
        self.shapes = tuple(tuple(s) for s in shapes)
        self.sizes = [int(np.prod(s)) for s in self.shapes]
        self.metric = {n: 1.0 for n in self.names}
        if metric:
            self.metric.update(metric)

    @property
    def size(self):
        return int(sum(self.sizes))

    def flatten(self, fields):
        return np.concatenate([np.asarray(f, dtype=float).ravel() for f in fields])

    def unflatten(self, vec):
        out, i = [], 0
        for shape, sz in zip(self.shapes, self.sizes):
            out.append(np.asarray(vec[i:i + sz]).reshape(shape))
            i += sz
        return tuple(out)

    def inner(self, a, b):
        """Weighted inner product sum_f metric[f] <a_f, b_f>."""
        fa, fb = self.unflatten(a), self.unflatten(b)
        return float(sum(self.metric[n] * np.sum(x * y) for n, x, y in zip(self.names, fa, fb)))

    def norm(self, a):
        return float(np.sqrt(max(self.inner(a, a), 0.0)))

    def normalized(self, a):
        n = self.norm(a)
        return a / n if n > 0 else a
