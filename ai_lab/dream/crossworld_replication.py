"""Independent replication shadow for *current* Cross-World leads.

The ordinary Multi-World comparator uses one seed per world each burst, so interesting matches can
appear and disappear.  This module spends extra compute only when that primary comparator actually
finds a lead.  It reruns the matched *other-world* zero condition with fresh seeds and asks whether the
same g001 X fingerprint matches again.

It deliberately does NOT update the cumulative CWX ledger: replication evidence is kept in a separate
shadow report so three confirmation attempts cannot inflate recurrent-signature counts.  A hit is never
called universality or identical physics, and the lane cannot change Rooms, official Levels, hypothesis
confidence or world dynamics.
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


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


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


def _match_for_pattern(matches: list[dict[str, Any]], pattern_id: str, pair: str) -> dict[str, Any] | None:
    for row in matches:
        if str(row.get("g001_pattern_id")) != str(pattern_id):
            continue
        if pair in (row.get("matched_world_zero_pairs") or []):
            return row
    return None


def replicate_current_leads(
    *, base_seed: int, replicates: int = 3, quick: bool = True,
    max_matches: int = 2, max_targets_per_match: int = 2,
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
        targets = []
        for raw in lead.get("matched_world_zero_pairs") or []:
            parsed = _pair(str(raw))
            if parsed is not None:
                targets.append((str(raw), parsed[0], parsed[1]))
        for pair_name, world_id, zero_id in targets[: max(0, int(max_targets_per_match))]:
            attempts = []
            for i in range(requested):
                seed = _seed(base_seed, pid, pair_name, i)
                try:
                    probe = cross_world_emergence.common_probe(
                        world_id, zero_id=zero_id, seed=seed, quick=bool(quick)
                    )
                    episodes = cross_world_emergence.detect_common_episodes(probe, max_episodes=3)
                    matches = cross_world_emergence.compare_g001_patterns(episodes=episodes, g001_ledger=g001)
                    hit = _match_for_pattern(matches, pid, pair_name)
                    attempts.append({
                        "seed": seed,
                        "finite": bool(probe.get("finite")),
                        "episodes": len(episodes),
                        "matched_again": hit is not None,
                        "status": None if hit is None else hit.get("status"),
                        "projection_coverage": None if hit is None else hit.get("projection_coverage"),
                        "strict_ZA_alignment": False if hit is None else bool(hit.get("strict_ZA_alignment")),
                    })
                except Exception as exc:
                    attempts.append({"seed": seed, "finite": False, "matched_again": False, "error": f"{type(exc).__name__}: {exc}"})
                    errors.append({"pattern_id": pid, "target": pair_name, "error": f"{type(exc).__name__}: {exc}"})
            finite = [x for x in attempts if x.get("finite")]
            hits = sum(bool(x.get("matched_again")) for x in finite)
            strict_hits = sum(bool(x.get("strict_ZA_alignment")) for x in finite if x.get("matched_again"))
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
        "version": 1,
        "mode": "cross-world-independent-replication-shadow",
        "triggered": bool(leads),
        "trigger_condition": "primary Cross-World comparator found at least one g001 pattern match in this burst",
        "primary_strict_zero_aligned_matches": int(current.get("strict_zero_aligned_matches", 0) or 0),
        "primary_signature_overlap_only_matches": int(current.get("signature_overlap_only_matches", 0) or 0),
        "replicates_per_target": requested,
        "results": rows,
        "errors": errors,
        "integrity": {
            "updates_cumulative_CWX_ledger": False,
            "changes_world_dynamics": False,
            "changes_hypothesis_confidence": False,
            "changes_official_level": False,
            "promotes_rooms": False,
            "same_fingerprint_means_same_physics": False,
            "universality_claim": False,
            "target_outcome_seeded": False,
            "fresh_sampling_seeds_are_physical_claims": False,
        },
        "interpretation": (
            "A repeated match makes a Cross-World lead less dependent on one target-world seed, but it still does not "
            "establish identical physics, a common conserved quantity, a common defect, causality, or universality."
        ),
    }


def write_report(report: dict[str, Any], output: Path = _OUTPUT) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return str(output)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Conditional independent Cross-World replication shadow")
    ap.add_argument("--base-seed", type=int, default=0)
    ap.add_argument("--replicates", type=int, default=3)
    ap.add_argument("--max-matches", type=int, default=2)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-record", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if a.no_record:
        dry_run.activate()
    report = replicate_current_leads(
        base_seed=a.base_seed, replicates=max(1, a.replicates), quick=a.quick,
        max_matches=max(0, a.max_matches),
    )
    out = write_report(report)
    print("=== Cross-World independent replication shadow ===")
    print(f"  triggered={report['triggered']} targets={len(report['results'])} errors={len(report['errors'])}")
    for row in report["results"]:
        print(f"  {row['g001_pattern_id']} -> {row['target_world_zero']}: {row['repeat_hits']}/{row['finite_replicates']}")
    print(f"  report={out}")
    print("  NOTE: repeated fingerprints are leads only; no universality/identical-physics claim.")
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())