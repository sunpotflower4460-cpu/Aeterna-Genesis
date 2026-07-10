"""Regression test for e031 (causal-set action smearing: H008 obstacle + partial cure) [frontier]."""

import importlib.util
import json
import os


def _load(name):
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e031_causal_action_smearing", name))
    spec = importlib.util.spec_from_file_location("e031_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_raw_fluctuates_smearing_damps():
    S = _load("smearing.py")
    r = S.simulate(quick=True)
    passed, checks = S.evaluate(r, quick=True)
    assert passed, checks
    # raw std vastly exceeds smeared at every N; smearing damps by a large factor at the largest N
    assert r["raw_exceeds_smeared_all_N"]
    assert r["smearing_damp_factor"] > 5.0


def test_bd_special_cases_via_core():
    """The BD action used here matches core.causet on the exact special cases (chain / antichain)."""
    import numpy as np
    from core.causet import bd_action_2d
    S = _load("smearing.py")
    N = 8
    chain = np.zeros((N, N), bool)
    for i in range(N):
        for j in range(i + 1, N):
            chain[i, j] = True
    assert S._bd_raw(chain) == bd_action_2d(chain) == N
    assert S._bd_raw(np.zeros((N, N), bool)) == N


def test_committed_result_sane():
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "experiments", "e031_causal_action_smearing",
        "results", "smearing.json"))
    assert os.path.exists(path)
    with open(path) as f:
        r = json.load(f)["result"]
    assert r["raw_exceeds_smeared_all_N"] and r["smearing_damp_factor"] > 5.0
