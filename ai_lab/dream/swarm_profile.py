"""Deterministic compute profiles for the production autonomous exploration swarm.

The Dream loop already explores every hour.  This module adds *orthogonal* specialist bursts without
changing physics, initial-condition semantics, scientific gates, Rooms or official Levels.  Specialist
profiles only reallocate existing search knobs so extra compute asks different questions instead of
repeating the same broad sweep.

Schedules are interpreted as planning metadata only.  They never enter a simulator as a physical
parameter and never seed a target morphology, event location, event time or desired outcome.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SwarmProfile:
    name: str
    purpose: str
    trials: int
    native3d_trials: int
    repro_top: int
    repro_seeds: int
    compare_native3d_top: int
    geometry_top: int
    geometry_broad: int
    followup_trials_2d: int
    followup_trials_3d: int
    followup_max_leads: int
    fission_path_trials_2d: int
    fission_path_max_leads: int
    deep_time_max_leads: int
    open_ended_probes: int
    open_ended_max_episodes: int
    unknown_followup_max_patterns: int
    max_synthesized_hypotheses: int
    root_law_trials: int
    root_sizes: str
    root_steps: int
    emergent_field_trials: int
    frontier_experiments: int
    native_variants: int
    max_jobs: int
    workers: int = 4

    def cli_args(self) -> list[str]:
        pairs: tuple[tuple[str, Any], ...] = (
            ("--trials", self.trials),
            ("--native3d-trials", self.native3d_trials),
            ("--workers", self.workers),
            ("--repro-top", self.repro_top),
            ("--repro-seeds", self.repro_seeds),
            ("--compare-native3d-top", self.compare_native3d_top),
            ("--geometry-top", self.geometry_top),
            ("--geometry-broad", self.geometry_broad),
            ("--followup-trials-2d", self.followup_trials_2d),
            ("--followup-trials-3d", self.followup_trials_3d),
            ("--followup-max-leads", self.followup_max_leads),
            ("--fission-path-trials-2d", self.fission_path_trials_2d),
            ("--fission-path-max-leads", self.fission_path_max_leads),
            ("--deep-time-max-leads", self.deep_time_max_leads),
            ("--open-ended-probes", self.open_ended_probes),
            ("--open-ended-max-episodes", self.open_ended_max_episodes),
            ("--unknown-followup-max-patterns", self.unknown_followup_max_patterns),
            ("--max-synthesized-hypotheses", self.max_synthesized_hypotheses),
            ("--root-law-trials", self.root_law_trials),
            ("--root-sizes", self.root_sizes),
            ("--root-steps", self.root_steps),
            ("--emergent-field-trials", self.emergent_field_trials),
            ("--frontier-experiments", self.frontier_experiments),
            ("--native-variants", self.native_variants),
            ("--max-jobs", self.max_jobs),
        )
        args = ["--quick"]
        for flag, value in pairs:
            args.extend((flag, str(value)))
        return args


PROFILES: dict[str, SwarmProfile] = {
    # The existing production budget is kept byte-for-byte in spirit.  The extra specialist runs are
    # additive, so ordinary hourly evidence remains longitudinally comparable.
    "baseline": SwarmProfile(
        name="baseline",
        purpose="hourly broad discovery and existing adaptive portfolio",
        trials=2048,
        native3d_trials=100,
        repro_top=8,
        repro_seeds=3,
        compare_native3d_top=12,
        geometry_top=16,
        geometry_broad=32,
        followup_trials_2d=256,
        followup_trials_3d=32,
        followup_max_leads=4,
        fission_path_trials_2d=24,
        fission_path_max_leads=2,
        deep_time_max_leads=1,
        open_ended_probes=24,
        open_ended_max_episodes=3,
        unknown_followup_max_patterns=2,
        max_synthesized_hypotheses=3,
        root_law_trials=24,
        root_sizes="8,12,16",
        root_steps=48,
        emergent_field_trials=12,
        frontier_experiments=24,
        native_variants=1,
        max_jobs=12,
    ),
    "novelty": SwarmProfile(
        name="novelty",
        purpose="widen open-ended transition discovery and falsifiable unknown-pattern followups",
        trials=1024,
        native3d_trials=80,
        repro_top=6,
        repro_seeds=3,
        compare_native3d_top=10,
        geometry_top=12,
        geometry_broad=24,
        followup_trials_2d=192,
        followup_trials_3d=24,
        followup_max_leads=4,
        fission_path_trials_2d=16,
        fission_path_max_leads=1,
        deep_time_max_leads=1,
        open_ended_probes=72,
        open_ended_max_episodes=5,
        unknown_followup_max_patterns=6,
        max_synthesized_hypotheses=6,
        root_law_trials=24,
        root_sizes="8,12,16",
        root_steps=48,
        emergent_field_trials=18,
        frontier_experiments=56,
        native_variants=1,
        max_jobs=12,
    ),
    "native3d": SwarmProfile(
        name="native3d",
        purpose="challenge 2D leads with more independent native-3D, geometry and deep-time evidence",
        trials=768,
        native3d_trials=200,
        repro_top=10,
        repro_seeds=3,
        compare_native3d_top=24,
        geometry_top=28,
        geometry_broad=56,
        followup_trials_2d=128,
        followup_trials_3d=64,
        followup_max_leads=4,
        fission_path_trials_2d=24,
        fission_path_max_leads=2,
        deep_time_max_leads=2,
        open_ended_probes=24,
        open_ended_max_episodes=3,
        unknown_followup_max_patterns=3,
        max_synthesized_hypotheses=3,
        root_law_trials=24,
        root_sizes="8,12,16",
        root_steps=48,
        emergent_field_trials=12,
        frontier_experiments=40,
        native_variants=2,
        max_jobs=16,
    ),
    "mechanism": SwarmProfile(
        name="mechanism",
        purpose="spend extra compute on interventions, breakers, root ablations and competing explanations",
        trials=1024,
        native3d_trials=80,
        repro_top=10,
        repro_seeds=3,
        compare_native3d_top=12,
        geometry_top=16,
        geometry_broad=32,
        followup_trials_2d=448,
        followup_trials_3d=32,
        followup_max_leads=6,
        fission_path_trials_2d=48,
        fission_path_max_leads=4,
        deep_time_max_leads=2,
        open_ended_probes=40,
        open_ended_max_episodes=4,
        unknown_followup_max_patterns=6,
        max_synthesized_hypotheses=8,
        root_law_trials=64,
        root_sizes="8,12,16,24",
        root_steps=64,
        emergent_field_trials=36,
        frontier_experiments=80,
        native_variants=1,
        max_jobs=16,
    ),
}

# Six specialist opportunities per UTC day, which are 01:07/05:07/09:07/13:07/17:07/21:07 JST.
# Every profile therefore gets two independent scheduled opportunities per day.
SCHEDULE_PROFILE: dict[str, str] = {
    "17 * * * *": "baseline",
    "47 * * * *": "baseline",  # watchdog only; normally exits before research
    "7 0,12 * * *": "novelty",
    "7 4,16 * * *": "native3d",
    "7 8,20 * * *": "mechanism",
}

SPECIALIST_RUNS_PER_DAY: dict[str, int] = {"novelty": 2, "native3d": 2, "mechanism": 2}


def choose_profile(*, event_name: str, schedule: str = "", manual_profile: str = "auto") -> SwarmProfile:
    manual = str(manual_profile or "auto").strip().lower()
    if manual != "auto":
        if manual not in PROFILES:
            raise ValueError(f"unknown exploration profile: {manual_profile!r}")
        return PROFILES[manual]
    if str(event_name) == "schedule":
        return PROFILES[SCHEDULE_PROFILE.get(str(schedule), "baseline")]
    return PROFILES["baseline"]


def daily_budget_summary() -> dict[str, Any]:
    """Return nominal scheduled budgets, not claims that every scheduled run completes."""
    run_counts = {"baseline": 24, **SPECIALIST_RUNS_PER_DAY}
    keys = (
        "trials",
        "native3d_trials",
        "open_ended_probes",
        "unknown_followup_max_patterns",
        "frontier_experiments",
        "emergent_field_trials",
        "root_law_trials",
        "deep_time_max_leads",
    )
    totals = {key: 0 for key in keys}
    for name, runs in run_counts.items():
        profile = PROFILES[name]
        for key in keys:
            totals[key] += int(getattr(profile, key)) * int(runs)
    return {
        "scheduled_research_opportunities_per_day": sum(run_counts.values()),
        "hourly_baseline_runs": 24,
        "specialist_runs": sum(SPECIALIST_RUNS_PER_DAY.values()),
        "specialist_runs_by_profile": dict(SPECIALIST_RUNS_PER_DAY),
        "nominal_budget_totals": totals,
        "watchdog_checks_not_counted": 24,
        "completion_is_not_guaranteed": True,
        "changes_physics": False,
        "changes_truth_gates": False,
        "seeds_target_outcomes": False,
    }


def _write_github_output(profile: SwarmProfile, path: str) -> None:
    output = Path(path)
    args = " ".join(profile.cli_args())
    with output.open("a", encoding="utf-8") as fh:
        fh.write(f"profile={profile.name}\n")
        fh.write(f"purpose={profile.purpose}\n")
        fh.write(f"args={args}\n")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Select an Aeterna autonomous exploration swarm profile")
    ap.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", "manual"))
    ap.add_argument("--schedule", default=os.environ.get("GITHUB_EVENT_SCHEDULE", ""))
    ap.add_argument("--manual-profile", default=os.environ.get("AETERNA_MANUAL_PROFILE", "auto"))
    ap.add_argument("--emit-github-output", action="store_true")
    ap.add_argument("--daily-summary", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.daily_summary:
        print(json.dumps(daily_budget_summary(), indent=2, ensure_ascii=False))
        return 0
    profile = choose_profile(
        event_name=args.event_name,
        schedule=args.schedule,
        manual_profile=args.manual_profile,
    )
    if args.emit_github_output:
        path = os.environ.get("GITHUB_OUTPUT")
        if not path:
            raise RuntimeError("--emit-github-output requires GITHUB_OUTPUT")
        _write_github_output(profile, path)
    else:
        print(json.dumps({**asdict(profile), "cli_args": profile.cli_args()}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
