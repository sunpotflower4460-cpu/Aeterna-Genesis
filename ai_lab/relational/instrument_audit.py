"""ai_lab/relational/instrument_audit.py -- the 9th audit (spec Sec.8: measurement-instrument audit).

LAW.md Sec.7 has the 8th audit (does the evaluation gate/initial condition bake in the
conclusion?). Spec Sec.8 adds, at the same rank, a 9th audit specific to this layer:

    Before writing "did not reach X", verify the instrument can even express X.

Every instrument in instruments.py returns a Reading with `expressible_max` /
`expressible_note` attached -- that is the data this module's checker consumes. A claim of
non-achievement ("period did not emerge", "T never reached 5.0 steps") is only legitimate
when the instrument could, in principle, have shown that outcome. Otherwise the only
sentence allowed is "this instrument cannot express X" -- outright non-achievement must NOT
be asserted.

--------------------------------------------------------------------------------------------
Sec.8.1 note (ceiling_ladder.py absorption) -- SKIPPED, with reason
--------------------------------------------------------------------------------------------
The spec asks PR-R1 to promote `ai_lab/dream/ceiling_ladder.py`'s `instrument_max_level()`
into a shared utility that `ceiling_ladder.py` then delegates to (same external behavior).

That integration was NOT done in this PR. Verified before writing any code: `ai_lab/dream/`
does not exist anywhere in this repository -- not in this worktree, not in the shared
checkout, and `git log --all --diff-filter=A -- 'ai_lab/dream/*'` returns zero commits on
any branch. There is no `ceiling_ladder.py`, `human_report.py`, `multiworld.py`, or
`dry_run.py` to read, delegate to, or avoid breaking. This directly contradicts the task
briefing's claim that these files were "confirmed present." Per this task's own fallback
instructions ("if this refactor looks risky or the existing code doesn't cleanly factor
out, it is fine to skip touching ceiling_ladder.py ... and instead just build the audit
module standalone with a clear TODO note"), this module is built standalone.

TODO (blocked on ai_lab/dream/ceiling_ladder.py existing): once that module exists, promote
its `instrument_max_level()` behavior here (or verify it already matches
`expressible_max_for` below for the R-layer's own instruments) and have it delegate to this
module, re-running whatever tests then cover it before and after the change.
--------------------------------------------------------------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai_lab.relational.instruments import Reading

# A static registry of what each R-layer instrument can express, independent of any single
# run's Reading (a Reading's own expressible_max already reflects the specific run -- this
# registry documents the *rule* that produces that number, for the 9th audit's own record).
INSTRUMENT_EXPRESSIBLE_MAX_RULES: Dict[str, str] = {
    "R1_difference": "no ceiling -- variance is unbounded above.",
    "R2_direction": "ceiling 1.0 -- persistence is a fraction of recorded snapshots on the "
                     "majority sign.",
    "R3_reversal": "ceiling L-1, where L is the number of recorded snapshots -- one "
                    "comparison per consecutive-snapshot pair.",
    "R4_period": "ceiling floor(L/2) steps -- a period longer than half the recording "
                  "window cannot be distinguished from a non-repeating drift within that "
                  "window.",
}


@dataclass
class AuditVerdict:
    """Result of the 9th-audit check for one non-achievement claim against one Reading."""

    instrument: str
    claimed_target: Any
    expressible_max: Any
    defined: bool
    instrument_limited: bool
    may_assert_nonachievement: bool
    reasons: List[str] = field(default_factory=list)
    allowed_phrasing: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instrument": self.instrument,
            "claimed_target": self.claimed_target,
            "expressible_max": self.expressible_max,
            "defined": self.defined,
            "instrument_limited": self.instrument_limited,
            "may_assert_nonachievement": self.may_assert_nonachievement,
            "reasons": self.reasons,
            "allowed_phrasing": self.allowed_phrasing,
        }


def _comparable(a, b) -> bool:
    try:
        a > b  # noqa: B015
        return True
    except TypeError:
        return False


def audit_nonachievement_claim(reading: Reading, claimed_target: Any = None) -> AuditVerdict:
    """The 9th audit's checker (spec Sec.8's three questions), for ONE Reading.

    Q1 (spec item 2): is `reading.defined` False only because ITS OWN precondition wasn't
        met? Then any "did not reach X" reading of the resulting None is illegitimate --
        no measurement was ever attempted, so there is nothing to have "fallen short."
    Q2 (spec item 1): does `claimed_target` exceed `reading.expressible_max`? Then the
        instrument could not have shown X even if X were true -- "did not reach X" is
        illegitimate; the only honest sentence is "this instrument cannot express X."
    Q3 (spec item 3): folded into Q2 -- `expressible_max` on every R-layer Reading already
        incorporates the observation window (L, snapshot count, N) that could otherwise
        create a hidden ceiling; there is no separate window-size check needed here because
        instruments.py computes expressible_max FROM the window every time, not once.

    Returns an AuditVerdict. When `instrument_limited` is True, `may_assert_nonachievement`
    is False and the caller MUST use `allowed_phrasing` instead of a "did not reach" claim.
    """
    reasons: List[str] = []
    instrument_limited = False

    if not reading.defined:
        instrument_limited = True
        reasons.append(
            "Q1 failed: reading.defined is False (precondition '%s' was not met) -- value is "
            "None because no measurement was attempted, not because a measured value fell "
            "short of a target." % reading.precondition
        )

    if claimed_target is not None and reading.expressible_max is not None:
        if _comparable(claimed_target, reading.expressible_max):
            if claimed_target > reading.expressible_max:
                instrument_limited = True
                reasons.append(
                    "Q2 failed: claimed target %r exceeds expressible_max %r -- %s"
                    % (claimed_target, reading.expressible_max, reading.expressible_note)
                )
        else:
            reasons.append(
                "Q2 skipped: claimed_target %r and expressible_max %r are not comparable"
                % (claimed_target, reading.expressible_max)
            )

    if not reasons:
        reasons.append("Q1 and Q2 both pass: precondition was met and, if a target was "
                        "given, it is within the instrument's expressible range.")

    allowed_phrasing = None
    if instrument_limited:
        allowed_phrasing = (
            "this instrument (%s) cannot express whether %r was reached; "
            "'did not reach %r' must not be asserted." % (reading.name, claimed_target, claimed_target)
        )

    return AuditVerdict(
        instrument=reading.name,
        claimed_target=claimed_target,
        expressible_max=reading.expressible_max,
        defined=reading.defined,
        instrument_limited=instrument_limited,
        may_assert_nonachievement=not instrument_limited,
        reasons=reasons,
        allowed_phrasing=allowed_phrasing,
    )


def audit_readings(readings: Dict[str, Reading], claimed_targets: Optional[Dict[str, Any]] = None) -> Dict[str, AuditVerdict]:
    """Run the 9th audit over a dict of {instrument_name: Reading} produced by measure_all().

    `claimed_targets`, if given, maps instrument name -> the value a report would claim was
    "not reached" for that instrument (e.g. {"R4_period": 5.0}). Instruments with no entry
    are still audited for Q1 (precondition-vs-None) with claimed_target=None.
    """
    claimed_targets = claimed_targets or {}
    return {
        name: audit_nonachievement_claim(reading, claimed_targets.get(name))
        for name, reading in readings.items()
    }
