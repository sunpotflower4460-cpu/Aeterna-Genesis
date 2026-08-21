from __future__ import annotations

import json
from pathlib import Path

from ai_lab.dream import free_hypothesis_lab
from ai_lab.dream import research_continuity
from ai_lab.dream import research_maintenance
from ai_lab.dream import science_bridge
from ai_lab.dream import science_bridge_runner


REPO = Path(__file__).resolve().parents[1]


def _write(path: Path, value) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_curated_science_sources_have_unique_real_doi_and_safe_policy() -> None:
    registry = json.loads((REPO / "ai_lab/discoveries/science_bridge_sources.json").read_text())
    sources = registry["sources"]
    assert len(sources) >= 4
    dois = [science_bridge.normalize_doi(row.get("doi")) for row in sources if row.get("doi")]
    assert all(dois)
    assert len(dois) == len(set(dois))
    assert "10.1098/rstb.1952.0012" in dois
    assert "10.1038/nphys3984" in dois
    assert "10.1038/s41467-026-69940-w" in dois
    assert registry["policy"]["literature_claim_is_aeterna_evidence"] is False
    assert registry["policy"]["literature_inspired_run_counts_as_strict_zero"] is False


def test_science_directions_only_use_existing_free_lab_instruments() -> None:
    registry = json.loads((REPO / "ai_lab/discoveries/science_bridge_sources.json").read_text())
    directions = science_bridge.build_directions(registry)
    assert len(directions["directions"]) == 4
    for row in directions["directions"]:
        assert row["experiment_type"] in free_hypothesis_lab._LIBRARY
        assert row["counts_as_strict_zero_evidence"] is False
        assert row["may_promote_room_or_level"] is False
        assert row["translation_is_analogy_not_reproduction"] is True
        assert row["strict_transfer_question"]


def test_science_ledger_deduplicates_same_source_by_doi() -> None:
    existing = {"sources": []}
    rows = [
        {"doi": "https://doi.org/10.1/example", "title": "A", "cited_by_count": 1},
        {"doi": "10.1/EXAMPLE", "title": "A newer title", "cited_by_count": 2},
    ]
    ledger = science_bridge._merge_ledger(existing, rows, seen_at="2026-01-01T00:00:00Z")
    assert ledger["count"] == 1
    assert ledger["sources"][0]["key"] == "doi:10.1/example"
    assert ledger["policy"]["sources_are_deleted"] is False


def test_science_runner_snapshot_keeps_strict_boundary() -> None:
    snapshot = science_bridge_runner._science_snapshot({
        "generated_at": "x",
        "source_evidence_context": {"pairs": 2},
        "hypotheses": [{
            "hypothesis_id": "science-a",
            "experiment_type": "slow_quench",
            "source": "science-bridge:paper",
            "strict_transfer_question": "retest from zero",
            "finite_runs": 3,
            "delta_vs_unmodified_control": {"reference_score": 0.2},
            "orientation_priority_only": 0.2,
        }],
    })
    assert snapshot["literature_inspired_hypotheses"][0]["counts_as_strict_zero_evidence"] is False
    assert snapshot["integrity"]["paper_claim_is_aeterna_evidence"] is False
    assert snapshot["integrity"]["similar_result_means_same_physics"] is False


def _patch_continuity_files(monkeypatch, tmp_path: Path, *, unknown: dict, deep: dict | None = None) -> None:
    easy = {
        "burst_id": "dream-test",
        "geometry_summary": {
            "triangle_seen": 2,
            "fission_like_after_triangle": 1,
            "control_seen": 4,
            "fission_like_after_control": 3,
            "rate_given_triangle": 0.5,
            "rate_given_control": 0.75,
            "triangle_excess_rate": -0.25,
            "persistent_pair_seen": 3,
            "persistent_pair_only_seen": 2,
            "triad_local_energy_measured": 1,
            "energy_asymmetry_peak_preceded_geometry_collapse": 0,
            "local_energy_observation": {"energy_used_to_select_relation": False, "causality_claim": False},
        },
        "zero_to_fission_path": {"triangle_is_required": False},
    }
    mapping = {
        "_EASY": _write(tmp_path / "easy.json", easy),
        "_UNKNOWN": _write(tmp_path / "unknown.json", unknown),
        "_DEEP": _write(tmp_path / "deep.json", deep or {"leads": []}),
        "_FREE_LEDGER": _write(tmp_path / "free.json", {"runs": []}),
        "_FREE_REPORT": _write(tmp_path / "free_report.json", {}),
        "_SCIENCE_LEDGER": _write(tmp_path / "science.json", {"sources": []}),
        "_SCIENCE_DIRECTIONS": _write(tmp_path / "science_dirs.json", {"directions": []}),
        "_BACKLOG": _write(tmp_path / "backlog.json", {"entries": []}),
        "_INDEX": _write(tmp_path / "index.json", {"entries": []}),
        "_HEALTH": _write(tmp_path / "health.json", {"burst_id": "dream-test", "healthy": True}),
        "_CROSSWORLD": _write(tmp_path / "cross.json", {}),
        "_OUTPUT": tmp_path / "continuity.json",
        "_REPORT_MD": tmp_path / "continuity.md",
    }
    for name, path in mapping.items():
        monkeypatch.setattr(research_continuity, name, path)


def test_nonspecific_x_is_not_misclassified_as_specific(monkeypatch, tmp_path: Path) -> None:
    _patch_continuity_files(monkeypatch, tmp_path, unknown={"patterns": {
        "X-no": {
            "status": "REPEATED_NONSPECIFIC",
            "exact": {"hit": 10, "n": 20},
            "nearby": {"hit": 9, "n": 20},
            "contrast": {"hit": 1, "n": 20},
            "search_focus": {"family": "white", "knobs": {}},
        },
        "X-yes": {
            "status": "REPEATED_SPECIFIC_CANDIDATE",
            "exact": {"hit": 10, "n": 20},
            "nearby": {"hit": 0, "n": 20},
            "contrast": {"hit": 0, "n": 20},
            "search_focus": {"family": "white", "knobs": {}},
        },
    }})
    rows = {row["key"]: row for row in research_continuity._current_lessons()}
    assert rows["x:X-no"]["importance"] == "context"
    assert rows["x:X-no"]["snapshot"]["specific_candidate"] is False
    assert rows["x:X-yes"]["importance"] == "carry"
    assert rows["x:X-yes"]["snapshot"]["specific_candidate"] is True


def test_continuity_preserves_old_negative_lesson_when_no_longer_visible(monkeypatch, tmp_path: Path) -> None:
    _patch_continuity_files(monkeypatch, tmp_path, unknown={"patterns": {}})
    old = {
        "lessons": [{
            "key": "x:old-weakened",
            "kind": "unknown_transition",
            "lane": "strict/open-ended-followup",
            "importance": "carry",
            "priority": 65,
            "snapshot": {"status": "WEAKENED"},
            "first_seen_at": "old",
            "last_seen_at": "old",
            "last_seen_burst": "old-burst",
            "last_snapshot_hash": "abc",
            "times_seen": 1,
            "history_tail": [{"snapshot_hash": "abc", "snapshot": {"status": "WEAKENED"}}],
            "currently_visible": True,
        }]
    }
    doc = research_continuity.build(existing=old)
    row = next(row for row in doc["lessons"] if row["key"] == "x:old-weakened")
    assert row["currently_visible"] is False
    assert row["snapshot"]["status"] == "WEAKENED"
    assert doc["policy"]["important_old_lessons_are_deleted_when_not_visible"] is False
    assert doc["policy"]["negative_results_are_carried_forward"] is True


def test_deep_time_uses_prefix_qualified_history_without_claiming_regression() -> None:
    normalized = research_continuity._deep_effective({
        "lead_id": "deep-x",
        "baseline_F_depth": 4,
        "status": "TRANSITION_SEEN_VERIFYING",
        "history": [
            {"F_depth": 1, "scientific_usable": False, "legacy_semantics_unverified": True},
            {"F_depth": 6, "scientific_usable": True, "prefix_identity_status": "MATCH", "balance_collapse_seen": True},
        ],
    })
    assert normalized["scientific_usable"] is True
    assert normalized["effective_F_depth"] == 6
    assert normalized["prefix_identity"] == "MATCH"
    assert normalized["transition_seen"] is True
    assert normalized["quarantined_history_count"] == 1


def test_maintenance_missing_required_fails_closed(monkeypatch, tmp_path: Path) -> None:
    required = tmp_path / "required.json"
    optional = tmp_path / "optional.json"
    monkeypatch.setattr(research_maintenance, "_REPO", tmp_path)
    monkeypatch.setattr(research_maintenance, "_DISC", tmp_path / "discoveries")
    monkeypatch.setattr(research_maintenance, "_TRACKED_JSON", {"easy_latest": required, "research_continuity": optional})
    monkeypatch.setattr(research_maintenance, "_OPTIONAL_NAMES", {"research_continuity"})
    report, _ = research_maintenance.build(apply_safe=False)
    assert "easy_latest" in report["missing_required_files"]
    assert "research_continuity" in report["missing_optional_files"]
    assert report["healthy_for_automatic_organization"] is False
    assert report["destructive_cleanup_performed"] is False
    assert report["policy"]["negative_results_are_deleted"] is False


def test_maintenance_duplicate_identity_is_unhealthy(monkeypatch, tmp_path: Path) -> None:
    source = _write(tmp_path / "sources.json", {"sources": [{"id": "same", "doi": "a"}, {"id": "same", "doi": "b"}]})
    monkeypatch.setattr(research_maintenance, "_REPO", tmp_path)
    monkeypatch.setattr(research_maintenance, "_DISC", tmp_path / "discoveries")
    monkeypatch.setattr(research_maintenance, "_TRACKED_JSON", {"science_bridge_sources": source})
    monkeypatch.setattr(research_maintenance, "_OPTIONAL_NAMES", set())
    report, _ = research_maintenance.build(apply_safe=False)
    assert report["duplicate_identity_findings"]
    assert report["healthy_for_automatic_organization"] is False
