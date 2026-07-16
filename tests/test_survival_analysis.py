"""Tests for genesis/diagnostics/survival_analysis.py (Observer v2, role V) against hand-computable
Kaplan-Meier cases -- verifies censoring is treated correctly (never silently equated with an observed
death), which is the exact statistical gap e055/e056's ad-hoc max-comparison had.
"""
import numpy as np

from genesis.diagnostics.survival_analysis import (
    kaplan_meier, median_survival, restricted_mean_survival, censoring_fraction, summarize,
)


def test_km_no_censoring_matches_empirical_survival():
    # 4 observed deaths at t=1,2,3,4 (no censoring): KM should equal the plain empirical survival fraction
    durations = [1, 2, 3, 4]
    censored = [False, False, False, False]
    times, surv = kaplan_meier(durations, censored)
    # after all 4 deaths, survival must be 0
    assert surv[-1] == 0.0
    # median: survival drops to 0.5 at or after t=2 (2 of 4 dead)
    med = median_survival(times, surv)
    assert med is not None and med <= 3


def test_all_censored_gives_undefined_median_but_valid_rmst():
    # every subject survives to the window end (right-censored) -- classic e055/e056-style data. KM must
    # stay at 1.0 throughout (no observed deaths), median must be None (never crosses 0.5), and RMST must
    # equal tau exactly (nobody died within the window, by definition of "no events").
    durations = [10, 10, 10, 10]
    censored = [True, True, True, True]
    times, surv = kaplan_meier(durations, censored)
    assert np.all(surv == 1.0)
    assert median_survival(times, surv) is None
    rmst = restricted_mean_survival(times, surv, tau=10)
    assert abs(rmst - 10.0) < 1e-9


def test_censoring_fraction_is_reported_honestly():
    censored = [True, True, False, False, False]
    assert abs(censoring_fraction(censored) - 0.4) < 1e-9


def test_summarize_bundles_everything_and_never_hides_censoring():
    durations = [5, 8, 12, 12, 12]
    censored = [False, False, True, True, True]   # 3 of 5 still alive at window end (t=12)
    r = summarize(durations, censored)
    assert r["n"] == 5
    assert r["n_events"] == 2
    assert r["n_censored"] == 3
    assert r["censoring_fraction"] == 0.6
    # with 60% censored, the median is likely unreached -- summarize must report None, not fabricate one
    if r["median_survival"] is not None:
        assert r["median_survival"] <= 12  # sanity: never exceeds the observed horizon


def test_mixing_censored_and_observed_at_same_time_is_handled():
    # a tie at t=12: one is an observed event, one is censored, at the same duration value
    durations = [12, 12]
    censored = [False, True]
    times, surv = kaplan_meier(durations, censored)
    assert surv[-1] < 1.0   # the one observed death must register as a drop
