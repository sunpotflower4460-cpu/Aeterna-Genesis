"""Independent replication shadow for current Cross-World leads.

The primary comparator can produce a lead on one burst and not the next. This module spends extra
compute only when the *current* primary report contains a g001 match, then repeats the matched other-world
zero condition with fresh seeds.

Replication evidence is deliberately separate from the cumulative CWX ledger. A repeat hit is a lead,
not universality or proof of identical physics.

Stale-evidence rule
-------------------
Before a workflow starts the potentially expensive replication step it writes a tiny current-burst
``NOT_COMPLETED`` placeholder through :func:`prime_report`. If the compute process crashes or times out,
that placeholder remains instead of an older burst's ``replication_latest.json``. A numerical/startup
failure is therefore visible as incomplete instrumentation, never silently reused as current evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from ai_lab.dream import cross_world_emergence
from ai_lab.dream import dry_run

_REPO = Path(__file__).resolve().parents[2]
_CURRENT = _REPO / "ai_lab" / "reports" / "crossworld" / "latest.json"
_G001 = _REPO / "ai_lab" / "discoveries" / "emergence_graph.json"
_OUTPUT = _REPO / "ai_lab" / "reports" / "crossworld" / "replication_latest.json"
_EASY = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _current_burst_id() -> str:
    easy = _read(_EASY, {})
    return str(easy.get("burst_id") or "unknown-burst")


def _seed(base: int, *parts: Any) -> int:
    raw = "|".join([str(int(base)), *(str(x) for x in parts)]).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:12], 16) % 1_000_000_000 + 1


def _pair(raw: str) -> tuple[str, str] | None:
    if "@" not in str(raw):
        return None
    world, zero = str(raw).split("@", 1)
    if not world or not zero or world == "g001-tdgl":
        return None
    return world, zero


def _match_for_pattern(
    matches: list[dict[str, Any]], pattern_id: str, pair: str,
) -> dict[str, Any] | None:
    for row in matches:
        if str(row.get("g001_pattern_id")) != str(pattern_id):
            continue
        if pair in (row.get("matched_world_zero_pairs") or []):
            return row
    return None


def _integrity() -> dict[str, bool]:
    return {
        "updates_cumulative_CWX_ledger": False,
        "changes_world_dynamics": False,
        "changes_hypothesis_confidence": False,
        "changes_official_level": False,
        "promotes_rooms": False,
        "same_fingerprint_means_same_physics": False,
        "universality_claim": False,
        "target_outcome_seeded": False,
        "fresh_sampling_seeds_are_physical_claims": False,
        "incomplete_or_failed_run_is_physical_negative_evidence": False,
    }


def prime_report(*, burst_id: str | None = None, base_seed: int = 0) -> dict[str, Any]:
    """Write a current-burst incomplete marker before expensive compute starts.

    This is operational evidence only. If it survives because a later step timed out, users know that
    independent replication did *not complete*; they must not read an older report as if it belonged to
    the new burst.
    """
    return {
        "version": 2,
        "mode": "cross-world-independent-replication-shadow",
        "burst_id": str(burst_id or _current_burst_id()),
        "completed": False,
        "completion_status": "NOT_COMPLETED",
        "triggered": False,
        "trigger_condition": "current primary comparator has not yet been independently replicated",
        "primary_strict_zero_aligned_matches": None,
        "primary_signature_overlap_only_matches": None,
        "replicates_per_target": 0,
        "results": [],
        "errors": [],
        "operational_note": (
            "Current-burst placeholder written before replication compute. If this remains, the "
            "replication step was interrupted or never completed; it is not a scientific miss."
        ),
        "base_seed": int(base_seed),
        "integrity": _integrity(),
        "interpretation": "Independent Cross-World replication has not completed for this burst.",
    }


def failure_report(
    *, burst_id: str | None = None, reason: str, base_seed: int = 0,
) -> dict[str, Any]:
    report = prime_report(burst_id=burst_id, base_seed=base_seed)
    report["completion_status"] = "FAILED_OR_INTERRUPTED"
    report["errors"] = [{"scope": "replication-step", "error": str(reason)}]
    report["interpretation"] = (
        "Independent Cross-World replication did not complete. This is instrumentation/compute status, "
        "not evidence that the physical signature failed to replicate."
    )
    return report


def replicate_current_leads(
    *, base_seed: int, replicates: int = 3, quick: bool = True,
    max_matches: int = 2, max_targets_per_match: int = 2,
    burst_id: str | None = None,
) -> dict[str, Any]:
    current = _read(_CURRENT, {})
    leads = list(current.get("g001_pattern_matches") or [])[: max(0, int(max_matches))]
    g001 = _read(_G001, {"patterns": [], "recent_episodes": []})
    requested = max(1, int(replicates))

    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for lead in leads:
        pid = str(lead.get("g001_pattern_id") or "")
        if not pid:
            continue
        targets: list[tuple[str, str, str]] = []
        for raw in lead.get("matched_world_zero_pairs") or []:
            parsed = _pair(str(raw))
            if parsed is not None:
                targets.append((str(raw), parsed[0], parsed[1]))

        for pair_name, world_id, zero_id in targets[: max(0, int(max_targets_per_match))]:
            attempts: list[dict[str, Any]] = []
            for i in range(requested):
                seed = _seed(base_seed, pid, pair_name, i)
                try:
                    probe = cross_world_emergence.common_probe(
                        world_id, zero_id=zero_id, seed=seed, quick=bool(quick)
                    )
                    episodes = cross_world_emergence.detect_common_episodes(probe, max_episodes=3)
                    matches = cross_world_emergence.compare_g001_patterns(
                        episodes=episodes, g001_ledger=g001
                    )
                    hit = _match_for_pattern(matches, pid, pair_name)
                    attempts.append({
                        "seed": seed,
                        "finite": bool(probe.get("finite")),
                        "episodes": len(episodes),
                        "matched_again": hit is not None,
                        "status": None if hit is None else hit.get("status"),
                        "projection_coverage": None if hit is None else hit.get("projection_coverage"),
                        "strict_ZA_alignment": (
                            False if hit is None else bool(hit.get("strict_ZA_alignment"))
                        ),
                    })
                except Exception as exc:  # preserve per-seed compute failure, do not turn it into a miss
                    text = f"{type(exc).__name__}: {exc}"
                    attempts.append({
                        "seed": seed,
                        "finite": False,
                        "matched_again": False,
                        "error": text,
                        "counts_as_physical_miss": False,
                    })
                    errors.append({"pattern_id": pid, "target": pair_name, "error": text})

            finite = [x for x in attempts if x.get("finite")]
            hits = sum(bool(x.get("matched_again")) for x in finite)
            strict_hits = sum(
                bool(x.get("strict_ZA_alignment"))
                for x in finite if x.get("matched_again")
            )
            rows.append({
                "g001_pattern_id": pid,
                "original_status": lead.get("status"),
                "g001_start_purities": lead.get("g001_start_purities") or [],
                "target_world_zero": pair_name,
                "original_projection_coverage": lead.get("projection_coverage"),
                "requested_replicates": requested,
                "finite_replicates": len(finite),
                "repeat_hits": hits,
                "strict_ZA_repeat_hits": strict_hits,
                "repeat_hit_rate": None if not finite else round(hits / len(finite), 4),
                "attempts": attempts,
            })

    return {
        "version": 2,
        "mode": "cross-world-independent-replication-shadow",
        "burst_id": str(burst_id or _current_burst_id()),
        "completed": True,
        "completion_status": "COMPLETED_WITH_ATTEMPT_ERRORS" if errors else "COMPLETED",
        "triggered": bool(leads),
        "trigger_condition": (
            "primary Cross-World comparator found at least one g001 pattern match in this burst"
        ),
        "primary_strict_zero_aligned_matches": int(
            current.get("strict_zero_aligned_matches", 0) or 0
        ),
        "primary_signature_overlap_only_matches": int(
            current.get("signature_overlap_only_matches", 0) or 0
        ),
        "replicates_per_target": requested,
        "results": rows,
        "errors": errors,
        "base_seed": int(base_seed),
        "integrity": _integrity(),
        "interpretation": (
            "A repeated match makes a Cross-World lead less dependent on one target-world seed, but it "
            "still does not establish identical physics, a common conserved quantity, a common defect, "
            "causality, or universality. Non-finite/errored attempts are not physical misses."
        ),
    }


def _compact_attachment(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": report.get("version"),
        "mode": report.get("mode"),
        "burst_id": report.get("burst_id"),
        "completed": bool(report.get("completed")),
        "completion_status": report.get("completion_status"),
        "triggered": bool(report.get("triggered")),
        "replicates_per_target": report.get("replicates_per_target"),
        "results": [
            {
                "g001_pattern_id": x.get("g001_pattern_id"),
                "original_status": x.get("original_status"),
                "g001_start_purities": x.get("g001_start_purities") or [],
                "target_world_zero": x.get("target_world_zero"),
                "original_projection_coverage": x.get("original_projection_coverage"),
                "finite_replicates": x.get("finite_replicates"),
                "repeat_hits": x.get("repeat_hits"),
                "strict_ZA_repeat_hits": x.get("strict_ZA_repeat_hits"),
                "repeat_hit_rate": x.get("repeat_hit_rate"),
            }
            for x in report.get("results") or []
        ],
        "errors": report.get("errors") or [],
        "integrity": report.get("integrity") or {},
        "interpretation": report.get("interpretation"),
        "full_report": "ai_lab/reports/crossworld/replication_latest.json",
    }


def write_report(report: dict[str, Any], output: Path = _OUTPUT) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    current = _read(_CURRENT, {})
    if isinstance(current, dict) and current:
        current["independent_replication_shadow"] = _compact_attachment(report)
        _CURRENT.parent.mkdir(parents=True, exist_ok=True)
        _CURRENT.write_text(json.dumps(current, indent=2, ensure_ascii=False))
    return str(output)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Conditional independent Cross-World replication shadow")
    ap.add_argument("--base-seed", type=int, default=0)
    ap.add_argument("--replicates", type=int, default=3)
    ap.add_argument("--max-matches", type=int, default=2)
    ap.add_argument("--burst-id", default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-record", action="store_true")
    ap.add_argument("--prime-only", action="store_true")
    ap.add_argument("--failure-only", action="store_true")
    ap.add_argument("--failure-reason", default="workflow-step-failed-or-interrupted")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if a.no_record:
        dry_run.activate()
    burst_id = str(a.burst_id or _current_burst_id())

    if a.prime_only:
        report = prime_report(burst_id=burst_id, base_seed=a.base_seed)
        write_report(report)
        print(f"Cross-World replication primed for {burst_id}")
        return 0
    if a.failure_only:
        report = failure_report(
            burst_id=burst_id, reason=a.failure_reason, base_seed=a.base_seed
        )
        write_report(report)
        print(f"Cross-World replication failure marker written for {burst_id}")
        return 0

    try:
        report = replicate_current_leads(
            base_seed=a.base_seed,
            replicates=max(1, a.replicates),
            quick=a.quick,
            max_matches=max(0, a.max_matches),
            burst_id=burst_id,
        )
    except Exception as exc:
        report = failure_report(
            burst_id=burst_id,
            reason=f"{type(exc).__name__}: {exc}",
            base_seed=a.base_seed,
        )
        write_report(report)
        print(f"Cross-World replication failed before completion: {type(exc).__name__}: {exc}")
        return 2

    out = write_report(report)
    print("=== Cross-World independent replication shadow ===")
    print(
        f"  burst={report['burst_id']} completed={report['completed']} "
        f"triggered={report['triggered']} targets={len(report['results'])} errors={len(report['errors'])}"
    )
    for row in report["results"]:
        print(
            f"  {row['g001_pattern_id']} -> {row['target_world_zero']}: "
            f"{row['repeat_hits']}/{row['finite_replicates']}"
        )
    print(f"  report={out}")
    print("  NOTE: repeated fingerprints are leads only; no universality/identical-physics claim.")
    # Per-attempt errors are preserved in a completed report. Return nonzero so workflow can surface the
    # instrumentation issue, while the already-written current-burst report prevents stale evidence.
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
