"""Production entry point: strict geometry controls + Adaptive Dream v4 follow-ups."""
from __future__ import annotations

import math

from ai_lab.dream import adaptive_v4
from ai_lab.dream import followups
from ai_lab.dream import strict_geometry as strict
from ai_lab.dream.strict_loop import _install_strict_geometry


def _install_strict_followup_geometry() -> None:
    # Follow-up triangle replays must use the same strict detector as the main geometry lane.
    followups.hourly._geometry_probe = strict._geometry_probe
    original_status = followups._update_status

    def update_status(lead):
        if lead.get("category") != "triangle-fission":
            return original_status(lead)
        # Do not weaken/strengthen a triangle lead merely because many replay runs contained no
        # qualifying triangle. Only actual strict triangle observations count toward this Lead.
        g = lead["evidence"]["geometry"]
        triangles = int(g.get("triangle", 0))
        split = int(g.get("fission_like", 0))
        if triangles >= 8 and split == 0:
            lead["status"] = "WEAKENED"
        elif triangles >= 8 and split >= 3:
            lead["status"] = "REPEATED_OBSERVATION"  # repeatability only; triangle causality stays separate
        else:
            lead["status"] = "VERIFYING"

    followups._update_status = update_status

    # The generic planner allocates 20% of each variant set to cheap 2D contrast tests. Direct-3D
    # verification intentionally excludes those contrast variants, so request a slightly larger
    # internal set and then report the ACTUAL number of 3D evaluations performed.
    original_run = followups.run_followups

    def run_followups_with_exact_3d_budget(doc, *, trials_3d=32, **kwargs):
        before = sum(int((x.get("evidence") or {}).get("native3d", {}).get("n", 0)) for x in doc.get("leads", []))
        requested = max(0, int(trials_3d))
        internal = 0 if requested == 0 else max(3, int(math.ceil(requested / 0.80)))
        result = original_run(doc, trials_3d=internal, **kwargs)
        after = sum(int((x.get("evidence") or {}).get("native3d", {}).get("n", 0)) for x in doc.get("leads", []))
        result["trials_3d"] = max(0, after - before)
        result["requested_trials_3d"] = requested
        return result

    followups.run_followups = run_followups_with_exact_3d_budget


def main(argv: list[str] | None = None) -> int:
    _install_strict_geometry()
    _install_strict_followup_geometry()
    return adaptive_v4.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
