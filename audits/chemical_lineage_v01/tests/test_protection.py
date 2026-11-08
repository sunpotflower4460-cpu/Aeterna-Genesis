"""T11, T14–T19: observers are read-only, convergence and SSA cross-checks, output guard, strict JSON,
negative values are reported and never clipped, and the pre-registration hash is consistent with the manifest."""
import glob
import hashlib
import json
import os

import numpy as np
import pytest

import _setup  # noqa: F401
import controls as C
import observers as O
import run_audit as RA
import strict_json as SJ

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_T11_observers_do_not_modify_their_inputs():
    st = C.run_arm("L1", 3, 2.0, 0.1, 2)
    before = st.copy()
    O.per_series_dispersion(st[:, 1])
    O.per_series_offset(st[:, 1], st[:, 2])
    O.complexed_unit_fraction(st[0, 1])
    O.reaction_usage(st[0, 1])
    assert np.array_equal(st, before)


def test_T11_observer_calls_do_not_change_the_run():
    a = C.run_arm("L1", 2, 2.0, 0.1, 3)
    st = C.run_arm("L1", 2, 2.0, 0.1, 3)
    O.per_series_dispersion(st[:, 1])
    b = C.run_arm("L1", 2, 2.0, 0.1, 3)
    assert np.array_equal(a, b)


def test_T14_tolerance_sequence_converges():
    import solver as S
    import thermodynamics as TH
    kf, kr = TH.forward_reverse_rates()
    start = C.seed_state(0)
    e = {rt: S.integrate(start, 2.0, kf, kr, rtol=rt, atol=rt * 1e-3)[1][-1] for rt in (1e-6, 1e-9, 1e-11)}
    assert np.max(np.abs(e[1e-9] - e[1e-11])) <= np.max(np.abs(e[1e-6] - e[1e-11]))
    assert np.max(np.abs(e[1e-9] - e[1e-11])) < 1e-6


def test_T15_ssa_matches_ode_for_single_association_within_error():
    import solver as S
    import thermodynamics as TH
    rng = np.random.default_rng(11)
    kf_all, kr_all = TH.forward_reverse_rates()
    kf, kr = float(kf_all[0]), float(kr_all[0])
    omega, runs = 200, 300
    _, Code = S.integrate(np.array([1.0, 1.0, 0, 0, 0, 0]), 1.0, kf_all, kr_all)
    vals = np.array([S.gillespie_xy(omega, omega, 0, omega, kf, kr, 1.0, rng)[2] / omega for _ in range(runs)])
    se = vals.std(ddof=1) / np.sqrt(runs)
    assert abs(vals.mean() - Code[-1, 3]) <= 4 * se + 1e-3


def test_T16_preregistration_is_valid_json_and_matches_manifest_when_a_run_exists():
    pre = os.path.join(HERE, "PRE_REGISTRATION.json")
    json.load(open(pre, encoding="utf-8"))
    for mf in glob.glob(os.path.join(HERE, "results", "**", "manifest.json"), recursive=True):
        m = json.load(open(mf, encoding="utf-8"))
        assert m["pre_registration_sha256"] == hashlib.sha256(open(pre, "rb").read()).hexdigest(), mf


def test_T17_missing_out_and_nonempty_directories_are_refused(tmp_path):
    with pytest.raises(RA.OutputRefused):
        RA.resolve_output_dir(None)
    (tmp_path / "x.csv").write_text("1")
    with pytest.raises(RA.OutputRefused):
        RA.resolve_output_dir(str(tmp_path))
    (tmp_path / "file.txt").write_text("1")
    with pytest.raises(RA.OutputRefused):
        RA.resolve_output_dir(str(tmp_path / "x.csv"))            # existing file
    new = RA.resolve_output_dir(str(tmp_path / "fresh"))
    assert os.path.isdir(new) and not os.listdir(new)


def test_T18_nonfinite_values_become_standard_json():
    out = SJ.finalize_summary({"a": float("nan"), "b": [1.0, float("inf")]})
    text = SJ.dumps(out)
    assert SJ.strict_loads(text)["a"] is None


def test_T19_negative_values_are_reported_and_never_clipped():
    """A negative concentration beyond tolerance is flagged by invariant_block and is left as it is."""
    base = C.seed_state(0)
    arr = np.zeros((1, 2, 6))
    arr[0, 0] = base
    arr[0, 1] = base
    arr[0, 1, 1] = -1e-3                       # injected negative value (not clipped)
    pr = {"negative_tolerance": 1e-9, "free_energy_increase_tolerance": 1e-10,
          "ssa": {}, "integrators": {}}
    import run_audit as R
    inv = R.invariant_block({"L1": arr}, 2.0, 0.1, 1, pr)
    assert inv["negative_below_tolerance_fail"] is True
    assert inv["min_concentration_L1"] == -1e-3
    assert arr[0, 1, 1] == -1e-3               # unchanged by the audit
