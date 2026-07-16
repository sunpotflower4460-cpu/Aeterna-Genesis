#!/usr/bin/env python3
"""Censoring-aware survival analysis (Observer v2) for episode/track durations.

Motivation (external review, 2026-07-16): e055/e056 compared the GLOBAL MAXIMUM duration across
independent seed sets at different observation-window lengths, and read a sub-proportional growth in the
max as evidence of "saturation" (a finite characteristic lifetime). This has two real statistical problems:
  1. A pair still bound when the observation window ends is RIGHT-CENSORED -- we only know it survived AT
     LEAST that long, not that it ended then. Treating "window ended" the same as "pair ended" biases
     duration statistics downward and can manufacture the appearance of saturation that isn't really there.
  2. Comparing the MAXIMUM of independent, differently-sized samples is dominated by extreme-value sampling
     noise, not the underlying survival distribution -- a bad estimator for "is there a finite lifetime".

Kaplan-Meier is the standard nonparametric estimator that correctly accounts for censoring, and the
restricted mean survival time (RMST, area under the KM curve up to a fixed horizon tau) is a well-defined
summary even when the median is never reached (heavy censoring). This module provides both, plus explicit
censoring-fraction reporting -- no result here silently treats "still alive" as "dead at the window edge".
"""
import numpy as np


def kaplan_meier(durations, censored):
    """durations: array of observed/censored times (>=0). censored: bool array, True = right-censored
    (still alive/bound when observation stopped). Returns (times, survival) as a right-continuous step
    function: survival[i] is P(T > times[i]).
    """
    durations = np.asarray(durations, dtype=float)
    censored = np.asarray(censored, dtype=bool)
    if len(durations) == 0:
        return np.array([0.0]), np.array([1.0])
    order = np.argsort(durations)
    d = durations[order]
    c = censored[order]
    n_at_risk = len(d)
    times, surv = [0.0], [1.0]
    s = 1.0
    i = 0
    while i < len(d):
        t = d[i]
        j = i
        events_here = 0
        while j < len(d) and d[j] == t:
            if not c[j]:
                events_here += 1
            j += 1
        if events_here > 0 and n_at_risk > 0:
            s *= (1.0 - events_here / n_at_risk)
        n_at_risk -= (j - i)
        times.append(float(t))
        surv.append(s)
        i = j
    return np.array(times), np.array(surv)


def median_survival(times, surv):
    """First time at which survival drops to <= 0.5, or None if the median is never reached (the KM curve
    never crosses 0.5 -- typically because of heavy right-censoring at the tail; report None, do not
    silently substitute the last observed time)."""
    below = np.where(surv <= 0.5)[0]
    return float(times[below[0]]) if len(below) else None


def restricted_mean_survival(times, surv, tau):
    """RMST: area under the KM step function from 0 to tau. Always well-defined (unlike the median), so
    this is the primary summary this module recommends for "how long do episodes typically last"."""
    if tau <= 0:
        return 0.0
    t = np.clip(times, 0, tau)
    area = 0.0
    for i in range(len(t) - 1):
        if t[i] >= tau:
            break
        area += surv[i] * (min(t[i + 1], tau) - t[i])
    if t[-1] < tau:
        area += surv[-1] * (tau - t[-1])
    return float(area)


def censoring_fraction(censored):
    censored = np.asarray(censored, dtype=bool)
    return float(np.mean(censored)) if len(censored) else 0.0


def summarize(durations, censored, tau=None):
    """One-call summary: KM curve + median (or None) + RMST + censoring fraction + event/sample counts.
    Always report censoring_fraction alongside any duration statistic -- a high fraction means the data
    cannot distinguish 'finite lifetime' from 'window too short', and that must be stated, not hidden."""
    durations = np.asarray(durations, dtype=float)
    censored = np.asarray(censored, dtype=bool)
    times, surv = kaplan_meier(durations, censored)
    if tau is None:
        tau = float(np.max(durations)) if len(durations) else 0.0
    return dict(median_survival=median_survival(times, surv),
                restricted_mean_survival=round(restricted_mean_survival(times, surv, tau), 4),
                censoring_fraction=round(censoring_fraction(censored), 4),
                n=int(len(durations)), n_events=int(np.sum(~censored)),
                n_censored=int(np.sum(censored)), tau=round(tau, 4),
                km_times=[round(float(x), 4) for x in times],
                km_survival=[round(float(x), 4) for x in surv])
