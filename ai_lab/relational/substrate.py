"""ai_lab/relational/substrate.py -- the R-layer basis: nodes, a relation graph, real state.

MODULE:      relational.substrate
QUESTION:    Starting from nothing but node indices, a relation graph, and a real-valued
             per-node state -- no coordinates, no complex numbers, no phase, no S^1 -- does
             *any* form of repetition emerge from differences alone, and if so, under which
             switchable ingredient is it present or absent?
PUT IN:      node count N (indices only, no coordinates); a relation graph G with weights
             w_ij >= 0 from a disclosed generation RULE (topology.py); real state x_i in R^m
             (default m=1); the local update rule (Sec.4.2, difference-only diffusion, plus
             optionally a per-node cubic saturation term, memory/inertia, weight plasticity,
             a conservation projection); a fixed timestep dt (numerical regulator, not
             physics); a small random initial inhomogeneity epsilon (no shape/pattern).
EMERGED:     see run.py / AUDIT.md for the measured contrast (memory=off vs memory=on).
CLAIM TIER:  measured (this module only produces trajectories + the raw ingredient labels;
             claim tier is assigned per-Reading in instruments.py / per-result in run.py).
KNOWN MATCH: N/A -- first measurement (R-layer PR-R1).
AUDIT (7):   see ai_lab/relational/AUDIT.md.
STATUS:      see ai_lab/relational/AUDIT.md.
A_OR_B:      (B)-leaning, but not (B). Still hand-set: the existence of the node set / the
             relation-graph generation rule / the update rule's functional form / the
             timestep / the initial small inhomogeneity / the finite node count.

HARD CONSTRAINT (spec Sec.4.2, tied to LAW.md's 8th audit): the relational core of the
update rule references ONLY the difference (x_j - x_i) over graph edges -- never absolute
position (nodes have none), never an absolute target value, and never a global aggregate
(mean/sum) UNLESS that reference is itself the explicit, disclosed "conservation" ingredient
axis (default OFF). At the all-minimal defaults (memory=off, saturation=none,
conservation=off, plasticity=off), the entire right-hand side of the ODE is exactly
-L @ x where L is the graph Laplacian -- a pure difference operator, nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np

from ai_lab.relational import topology as topo

# ---------------------------------------------------------------------------
# Ingredient axes (spec Sec.4.3). Every axis below MUST appear both as a keyword argument
# here and as a key in the dict returned by run(). Defaults are all on the minimal side.
# ---------------------------------------------------------------------------
DEFAULT_MEMORY = "off"              # "off" (first-order relaxation) | "on" (second-order/inertial)
DEFAULT_SATURATION = "none"         # "none" | "cubic"
DEFAULT_CONSERVATION = False        # off by default
DEFAULT_PLASTICITY = False          # off by default
DEFAULT_TOPOLOGY = topo.DEFAULT_TOPOLOGY  # "random_regular" -- never "grid" by default
DEFAULT_M = 1                       # real dimension of node state, default minimal

def _default_random_regular_degree(n: int) -> int:
    """Pick a degree <= min(4, n-1). Any value here works: if n is even, n*degree is even
    for any degree; if n is odd, n-1 is even, so capping at n-1 when n-1 < 4 always yields
    an even degree too -- random_regular's own n*degree-even precondition is always
    satisfied by this choice, for every n >= 2."""
    return min(4, n - 1)


_TOPOLOGY_DEFAULT_KWARGS = {
    "random_regular": lambda n: {"degree": _default_random_regular_degree(n)},
    "erdos_renyi": lambda n: {"p": min(1.0, 4.0 / max(n - 1, 1))},
    "watts_strogatz": lambda n: {"k": 4 if n > 4 else 2, "beta": 0.1},
    "barabasi_albert": lambda n: {"m": 2 if n > 2 else 1},
    "grid": lambda n: {"dim": 1},
}


def _default_topology_kwargs(name: str, n: int) -> Dict[str, Any]:
    fn = _TOPOLOGY_DEFAULT_KWARGS.get(name)
    return dict(fn(n)) if fn else {}


def initial_state(n: int, m: int, epsilon: float, seed: Optional[int]) -> np.ndarray:
    """Small random inhomogeneity, no shape/pattern placed. x_i(0) ~ N(0, epsilon^2), i.i.d.

    This is the ONE thing the substrate is allowed to hand-set as an initial condition
    (spec Sec.3/Sec.4.1): a scale (epsilon), not a shape. Any node ordering, any seed,
    produces a generic (non-special) starting point.
    """
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=epsilon, size=(n, m))


def _laplacian_diffusion(x: np.ndarray, W: np.ndarray) -> np.ndarray:
    """Sum_j w_ij (x_j - x_i) for every node i, i.e. -L @ x. Difference-only, no absolute term."""
    deg = W.sum(axis=1)
    return (W @ x) - deg[:, None] * x


def _saturation(x: np.ndarray, kind: str, strength: float) -> np.ndarray:
    """A per-node, self-referential nonlinearity that stops divergence (spec Sec.4.3).

    This is the one term in the equation that is NOT a difference between nodes -- it is
    disclosed explicitly as the switchable "saturation" ingredient axis and is OFF
    (strength effectively 0, kind="none") at the minimal default. It never references any
    other node or any aggregate quantity -- only the node's own state.
    """
    if kind == "none":
        return np.zeros_like(x)
    if kind == "cubic":
        return -strength * x ** 3
    raise ValueError("unknown saturation kind %r" % kind)


def _project_conserving(dv_or_dx: np.ndarray) -> np.ndarray:
    """Remove the across-node mean of an increment so that Sum_i (that state) is conserved.

    Only ever called when conservation=True (an explicit, disclosed ingredient axis -- spec
    Sec.4.3's "conservation" row: "does Sum(x) get conserved / do +/- appear paired?"). This
    is the one place the substrate is allowed to reference a global aggregate (the mean),
    and it is off by default.
    """
    return dv_or_dx - dv_or_dx.mean(axis=0, keepdims=True)


def _plasticity_step(x: np.ndarray, W: np.ndarray, mask: np.ndarray, eta: float, dt: float) -> np.ndarray:
    """dw_ij/dt = eta * ((x_j - x_i)^2 - w_ij), restricted to originally-existing edges.

    Depends only on the pairwise difference and the current weight -- never on an absolute
    node value or a global aggregate.
    """
    diff = x[None, :, :] - x[:, None, :]          # diff[i, j] = x_j - x_i
    sq = np.sum(diff ** 2, axis=-1)                # sum over the m state dimensions
    dW = eta * (sq - W)
    W_new = W + dt * dW * mask
    np.fill_diagonal(W_new, 0.0)
    W_new = np.clip(W_new, 0.0, None)
    # keep symmetric by construction (sq, W, mask are all symmetric already); average out
    # any float asymmetry from clip/fill just in case.
    W_new = 0.5 * (W_new + W_new.T)
    return W_new


def _rk4_first_order(x, dt, deriv):
    k1 = deriv(x)
    k2 = deriv(x + 0.5 * dt * k1)
    k3 = deriv(x + 0.5 * dt * k2)
    k4 = deriv(x + dt * k3)
    return x + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def _rk4_second_order(x, v, dt, deriv):
    k1x, k1v = deriv(x, v)
    k2x, k2v = deriv(x + 0.5 * dt * k1x, v + 0.5 * dt * k1v)
    k3x, k3v = deriv(x + 0.5 * dt * k2x, v + 0.5 * dt * k2v)
    k4x, k4v = deriv(x + dt * k3x, v + dt * k3v)
    nx = x + (dt / 6.0) * (k1x + 2 * k2x + 2 * k3x + k4x)
    nv = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return nx, nv


@dataclass
class SubstrateResult:
    """Raw simulation output. `to_dict()` is what run.py / instruments.py consume."""

    x_traj: np.ndarray            # shape (L+1, N, m) -- includes t=0
    v_traj: Optional[np.ndarray]  # shape (L+1, N, m) or None (memory=off)
    W_initial: np.ndarray         # shape (N, N)
    W_final: np.ndarray           # shape (N, N)
    n: int
    m: int
    steps: int
    dt: float
    seed: Optional[int]
    epsilon: float
    memory: str
    saturation: str
    saturation_strength: float
    conservation: bool
    plasticity: bool
    plasticity_rate: float
    damping: float
    topology: str
    topology_kwargs: Dict[str, Any]
    geometry_was_given: bool

    def to_dict(self, include_trajectory: bool = True) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "n": self.n,
            "m": self.m,
            "steps": self.steps,
            "dt": self.dt,
            "seed": self.seed,
            "epsilon": self.epsilon,
            # -- every ingredient axis, every run, no exceptions (spec Sec.4.3) --
            "memory": self.memory,
            "saturation": self.saturation,
            "saturation_strength": self.saturation_strength,
            "conservation": self.conservation,
            "plasticity": self.plasticity,
            "plasticity_rate": self.plasticity_rate,
            "damping": self.damping,
            "topology": self.topology,
            "topology_kwargs": self.topology_kwargs,
            "geometry_was_given": self.geometry_was_given,
            "sum_x_initial": float(self.x_traj[0].sum()),
            "sum_x_final": float(self.x_traj[-1].sum()),
        }
        if include_trajectory:
            d["x_traj"] = self.x_traj.tolist()
            if self.v_traj is not None:
                d["v_traj"] = self.v_traj.tolist()
        return d


def run(
    n: int = 40,
    steps: int = 2000,
    dt: float = 0.05,
    seed: Optional[int] = None,
    epsilon: float = 0.1,
    topology: str = DEFAULT_TOPOLOGY,
    topology_kwargs: Optional[Dict[str, Any]] = None,
    memory: str = DEFAULT_MEMORY,
    saturation: str = DEFAULT_SATURATION,
    saturation_strength: float = 0.1,
    conservation: bool = DEFAULT_CONSERVATION,
    plasticity: bool = DEFAULT_PLASTICITY,
    plasticity_rate: float = 0.02,
    m: int = DEFAULT_M,
    damping: float = 0.08,
) -> SubstrateResult:
    """Run the R-layer substrate. Every ingredient axis defaults to its minimal side.

    memory="off": dx_i/dt = Sum_j w_ij (x_j - x_i) + g(x_i)                  (Sec.4.2, first-order)
    memory="on":  dv_i/dt = Sum_j w_ij (x_j - x_i) + g(x_i) - damping * v_i   (Sec.4.2, second-order)
                  dx_i/dt = v_i
    where g(x_i) = -saturation_strength * x_i^3 when saturation="cubic" (spec Sec.4.2's
    "a*g(x_i)" term, with a folded into saturation_strength -- see `_saturation`), else 0.
    """
    if memory not in ("off", "on"):
        raise ValueError("memory must be 'off' or 'on'")
    if saturation not in ("none", "cubic"):
        raise ValueError("saturation must be 'none' or 'cubic'")
    if n < 2:
        raise ValueError("need n >= 2 nodes for a relation graph to mean anything")

    tk = dict(topology_kwargs) if topology_kwargs else _default_topology_kwargs(topology, n)
    W0 = topo.build_topology(topology, n, seed=seed, **tk)
    mask = (W0 > 0).astype(float)
    W = W0.copy()

    x0 = initial_state(n, m, epsilon, seed)
    x = x0.copy()
    x_hist = [x0.copy()]

    if memory == "off":
        def deriv(xx):
            # _saturation already applies saturation_strength internally (and returns exactly
            # zero when saturation="none") -- do NOT multiply by a coefficient again here.
            d = _laplacian_diffusion(xx, W) + _saturation(xx, saturation, saturation_strength)
            if conservation:
                d = _project_conserving(d)
            return d

        for _ in range(steps):
            x = _rk4_first_order(x, dt, deriv)
            if plasticity:
                W = _plasticity_step(x, W, mask, plasticity_rate, dt)
            x_hist.append(x.copy())
        v_hist_arr = None
    else:
        v = np.zeros_like(x0)
        v_hist = [v.copy()]

        def deriv2(xx, vv):
            dv = _laplacian_diffusion(xx, W) + _saturation(xx, saturation, saturation_strength) - damping * vv
            if conservation:
                dv = _project_conserving(dv)
            dx = vv
            return dx, dv

        for _ in range(steps):
            x, v = _rk4_second_order(x, v, dt, deriv2)
            if plasticity:
                W = _plasticity_step(x, W, mask, plasticity_rate, dt)
            x_hist.append(x.copy())
            v_hist.append(v.copy())
        v_hist_arr = np.stack(v_hist, axis=0)

    return SubstrateResult(
        x_traj=np.stack(x_hist, axis=0),
        v_traj=v_hist_arr,
        W_initial=W0,
        W_final=W,
        n=n,
        m=m,
        steps=steps,
        dt=dt,
        seed=seed,
        epsilon=epsilon,
        memory=memory,
        saturation=saturation,
        saturation_strength=saturation_strength if saturation != "none" else 0.0,
        conservation=conservation,
        plasticity=plasticity,
        plasticity_rate=plasticity_rate if plasticity else 0.0,
        damping=damping if memory == "on" else 0.0,
        topology=topology,
        topology_kwargs=tk,
        geometry_was_given=topo.geometry_was_given(topology),
    )
