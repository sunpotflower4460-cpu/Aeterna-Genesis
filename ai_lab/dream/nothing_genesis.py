"""Strict Nothing Genesis (NØ) meta-control.

This module deliberately does *less* than Pure Genesis R0.

NØ asks: if the physical side is given literally nothing, can a computation honestly report that
something physically emerged? The strict arm therefore supplies no entities, slots, state space,
initial state, relation, transition rule, time/order, randomness, probability measure, possibility set,
geometry, energy, or observer. It does not perform a hidden random draw and it does not call a zero
array "nothing".

That makes NØ a null/control experiment rather than a dynamical simulation. With no transition
semantics there is no physical step to execute. If this arm ever reports an object/event anyway, that
is treated as an implementation leak or an added assumption, never as ex-nihilo emergence.

The surrounding *meta* layer may enumerate candidate "first givens" to map the boundary between strict
nothing and runnable models. Enumeration is not itself a physical audit or simulation, and no nonempty
combination can count as strict-NØ evidence. In particular, "all things can happen" would itself require
at least a possibility/admissibility structure (and a measure or rule if one outcome is sampled), so it
is recorded as a boundary hypothesis but is not smuggled into the strict arm.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import zlib
from pathlib import Path
from typing import Any, Iterable

from ai_lab.dream import dry_run

_REPO = Path(__file__).resolve().parents[2]
_REPORT = _REPO / "ai_lab" / "reports" / "easy" / "nothing_latest.json"
_HUMAN = _REPO / "ai_lab" / "reports" / "easy" / "nothing_latest.md"
_SCREENSHOT = _REPO / "ai_lab" / "reports" / "easy" / "nothing_latest.png"
_ARCHIVE = _REPO / "ai_lab" / "reports" / "easy" / "nothing"
_EASY_LATEST = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"

FIRST_GIVEN_CANDIDATES: tuple[str, ...] = (
    "carrier_or_existence_domain",
    "entity_multiplicity",
    "identity",
    "distinguishability",
    "relation",
    "state_space",
    "initial_state",
    "change_possibility",
    "transition_rule_or_law",
    "ordering_or_time",
    "randomness",
    "probability_measure",
    "possibility_space_or_admissibility",
    "geometry_or_dimension",
    "energy_or_conservation_structure",
    "physical_observer_or_measurement_rule",
)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _latest_burst_id() -> str:
    """Standalone-CLI fallback only; integrated execution passes the triggering burst explicitly."""
    latest = _read(_EASY_LATEST, {})
    return str(latest.get("burst_id") or "unknown-burst")


def _safe_burst_id(value: Any) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "unknown-burst")).strip("-.")
    return text or "unknown-burst"


def _archive_paths(burst_id: str) -> dict[str, Path]:
    root = _ARCHIVE / _safe_burst_id(burst_id)
    return {"root": root, "report": root / "report.json", "human": root / "human.md", "screenshot": root / "boundary.png"}


def strict_nothing_control() -> dict[str, Any]:
    """Return the one strict NØ case. Reporting booleans are not a physical zero field or vacuum."""
    physical_layer = {
        "physical_givens": [],
        "entities_seeded": False,
        "entity_count_defined": False,
        "slots_defined": False,
        "identity_defined": False,
        "distinguishability_defined": False,
        "relations_defined": False,
        "state_space_defined": False,
        "initial_state_defined": False,
        "zero_field_defined": False,
        "vacuum_state_defined": False,
        "change_possibility_defined": False,
        "transition_rule_defined": False,
        "law_defined": False,
        "time_defined": False,
        "update_step_defined": False,
        "randomness_defined": False,
        "random_seed_defined": False,
        "probability_measure_defined": False,
        "possibility_space_defined": False,
        "geometry_defined": False,
        "dimension_defined": False,
        "energy_defined": False,
        "physical_observer_defined": False,
    }
    result = {
        "physical_transition_executed": False,
        "physical_event_defined": False,
        "something_observed": False,
        "outcome": "NO_PHYSICAL_DYNAMICS_DEFINED",
        "nothing_to_something_claim": False,
        "result_is_control_construction_not_independent_measurement": True,
        "interpretation": (
            "何も物理前提を与えない場合、計算上の『次』そのものを定義できない。"
            "これは『無から何かは絶対に生まれない』という形而上学的証明ではなく、"
            "追加前提なしには計算実験として状態遷移を判定できないという境界結果。"
        ),
    }
    return {
        "id": "NØ",
        "name": "strict-nothing",
        "strict_nothing": True,
        "physical_layer": physical_layer,
        "result": result,
        "meta_scaffolding": {
            "code_and_hardware_exist": True,
            "reporting_symbols_exist": True,
            "count_as_physical_givens": False,
            "note": "計算機・Python・JSONは観測装置側の足場であり、NØ内部の物理として数えない。",
        },
    }


def _iter_nonempty_subsets(names: tuple[str, ...]) -> Iterable[tuple[str, ...]]:
    n = len(names)
    for mask in range(1, 1 << n):
        yield tuple(names[i] for i in range(n) if mask & (1 << i))


def enumerate_first_given_boundary(names: tuple[str, ...] = FIRST_GIVEN_CANDIDATES) -> dict[str, Any]:
    """Enumerate added-assumption combinations; enumeration is not a physical audit."""
    if len(names) > 20:
        raise ValueError("boundary enumeration is intentionally capped at 20 named assumptions")
    digest = hashlib.sha256()
    by_size = {str(i): 0 for i in range(1, len(names) + 1)}
    singletons: list[list[str]] = []
    pair_examples: list[list[str]] = []
    total = 0
    for subset in _iter_nonempty_subsets(names):
        total += 1
        by_size[str(len(subset))] += 1
        digest.update(("|".join(subset) + "\n").encode("utf-8"))
        if len(subset) == 1:
            singletons.append(list(subset))
        elif len(subset) == 2 and len(pair_examples) < 32:
            pair_examples.append(list(subset))
    return {
        "mode": "meta-assumption-boundary-enumeration",
        "candidate_first_givens": list(names),
        "candidate_count": len(names),
        "nonempty_combinations_enumerated": total,
        "expected_nonempty_combinations": (1 << len(names)) - 1,
        "combinations_by_size": by_size,
        "canonical_enumeration_sha256": digest.hexdigest(),
        "single_assumption_frontier": singletons,
        "pair_examples": pair_examples,
        "per_combination_physical_simulation_performed": False,
        "per_combination_outcome_audit_performed": False,
        "every_nonempty_combination_is_strict_nothing": False,
        "every_nonempty_combination_counts_as_from_nothing_evidence": False,
        "purpose": "何かが出たように見えた時、どの『最初の与え物』を追加したかを追跡するための境界地図。",
    }


def audit_first_given_boundary(names: tuple[str, ...] = FIRST_GIVEN_CANDIDATES) -> dict[str, Any]:
    """Backward-compatible name. The returned object explicitly says enumeration-only."""
    return enumerate_first_given_boundary(names)


def possibility_zero_boundary() -> dict[str, Any]:
    return {
        "id": "N0-P",
        "label": "全てが起きうる0",
        "strict_nothing": False,
        "instantiated_in_strict_arm": False,
        "why_not_identical_to_nothing": [
            "『起きうる』と言うには、少なくとも可能/不可能を区別する意味が要る。",
            "具体的な候補集合を置けば possibility_space が追加前提になる。",
            "その中から何かを選ぶなら、選択規則・確率測度・乱数などが追加前提になる。",
        ],
        "policy": (
            "N0-Pは境界仮説として記録するだけで、strict NØには可能性集合・乱数・法則を入れない。"
            "将来N0-Pを実装する場合も『無から』ではなく『可能性構造を1つ与えた最小モデル』と明記する。"
        ),
    }


def _compact_r0_metadata(r0_metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(r0_metadata, dict) or not r0_metadata:
        return {"supplied_by_triggering_run": False}
    return {
        "supplied_by_triggering_run": True,
        "mode": r0_metadata.get("mode"),
        "root": r0_metadata.get("root") or {},
        "law_trials": r0_metadata.get("law_trials"),
        "sizes": r0_metadata.get("sizes") or [],
        "steps": r0_metadata.get("steps"),
        "why_gate": r0_metadata.get("why_gate") or {},
        "root_integrity_audit": r0_metadata.get("root_integrity_audit") or {},
        "not_claimed": r0_metadata.get("not_claimed") or [],
    }


def _technical_audit(strict: dict[str, Any], boundary: dict[str, Any], *, boundary_names: tuple[str, ...]) -> dict[str, Any]:
    strict_repeat = strict_nothing_control()
    boundary_repeat = enumerate_first_given_boundary(boundary_names)
    strict_same = strict_repeat == strict
    digest_same = boundary_repeat["canonical_enumeration_sha256"] == boundary["canonical_enumeration_sha256"]
    physical = strict.get("physical_layer") or {}
    result = strict.get("result") or {}
    return {
        "role": {"primary": "F", "secondary": ["N"]},
        "claim_tier": ["frontier"],
        "claim_scope": "software/meta-control boundary only; not an Emergence-role physical simulation",
        "physics_integrity_applicability": "NOT_A_PHYSICAL_SIMULATION",
        "no_touch": {
            "physics_dynamics_invoked": False,
            "downstream_state_injected_into_strict_arm": False,
            "official_rooms_written": False,
            "scientific_thresholds_changed": False,
            "promotion_gates_changed": False,
        },
        "eighth_audit": {
            "applicability": "NOT_APPLICABLE_AS_A_PASSED_PHYSICAL_EMERGENCE_AUDIT",
            "independent_physical_outcome_detector_exists": False,
            "constructor_sets_null_result": bool(result.get("result_is_control_construction_not_independent_measurement")),
            "invariant_checks": {
                "physical_givens_are_empty": physical.get("physical_givens") == [],
                "state_space_is_undefined": physical.get("state_space_defined") is False,
                "initial_state_is_undefined": physical.get("initial_state_defined") is False,
                "transition_rule_is_undefined": physical.get("transition_rule_defined") is False,
                "physical_transition_was_not_executed": result.get("physical_transition_executed") is False,
            },
            "declarations_not_independent_measurements": {
                "target_encoded": False,
                "initial_condition_contains_claim_quantity": False,
                "gate_encodes_claim_causality": False,
                "threshold_passes_by_target_construction": False,
                "claimed_quantity_is_algebraic_relabeling_of_input": False,
            },
            "verdict": "DECLARATIVE_NULL_CONTROL_NOT_A_PASSED_EIGHTH_AUDIT",
            "note": (
                "NØには初期条件・方程式・評価ゲート・独立outcome detector自体がない。"
                "something_observed=falseも測定結果ではなくnull-controlの構成値なので、第8監査を『passed』とは記録しない。"
            ),
        },
        "determinism": {
            "strict_control_repeat_identical": strict_same,
            "boundary_enumeration_digest_repeat_identical": digest_same,
            "passed": strict_same and digest_same,
        },
        "reproduction": {
            "standalone_command": "python -m ai_lab.dream.nothing_genesis --burst-id <id>",
            "dry_run_command": "python -m ai_lab.dream.nothing_genesis --burst-id <id> --no-record",
            "expected_strict_result": "physical givens=0; no physical transition; something_observed=false (constructor value, not measurement)",
            "expected_boundary_result": f"enumerates {(1 << len(boundary_names)) - 1} nonempty assumption combinations; does not simulate them as NØ",
        },
    }


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def _boundary_png(boundary: dict[str, Any], *, width: int = 720, height: int = 420) -> bytes:
    """Dependency-free meta visualization. It is deliberately not a picture of NØ physics."""
    width, height = max(320, int(width)), max(240, int(height))
    bg, ink, accent, warning = (247, 248, 250), (41, 52, 64), (74, 125, 180), (190, 111, 55)
    px = bytearray(bg * (width * height))

    def rect(x0: int, y0: int, x1: int, y1: int, rgb: tuple[int, int, int]) -> None:
        x0, x1 = max(0, x0), min(width, x1)
        y0, y1 = max(0, y0), min(height, y1)
        for y in range(y0, y1):
            start = (y * width + x0) * 3
            for x in range(x0, x1):
                idx = start + (x - x0) * 3
                px[idx:idx + 3] = bytes(rgb)

    rect(34, 35, width - 34, 39, ink)
    rect(42, 62, 54, height - 52, warning)
    counts = [int(boundary.get("combinations_by_size", {}).get(str(i), 0)) for i in range(1, int(boundary.get("candidate_count", 0)) + 1)]
    max_count = max(counts, default=1)
    plot_left, plot_right, plot_top, plot_bottom = 92, width - 38, 70, height - 52
    slots = max(1, len(counts))
    cell = max(4, (plot_right - plot_left) // slots)
    bar_w = max(2, int(cell * 0.62))
    for i, count in enumerate(counts):
        frac = 0.0 if count <= 0 else math.log1p(count) / math.log1p(max_count)
        h = max(2, int((plot_bottom - plot_top) * frac))
        x0 = plot_left + i * cell + (cell - bar_w) // 2
        rect(x0, plot_bottom - h, x0 + bar_w, plot_bottom, accent)
    rect(plot_left, plot_bottom, plot_right, plot_bottom + 2, ink)
    raw = b"".join(b"\x00" + bytes(px[y * width * 3:(y + 1) * width * 3]) for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", header) + _png_chunk(b"IDAT", zlib.compress(raw, 9)) + _png_chunk(b"IEND", b"")


def _human_markdown(report: dict[str, Any]) -> str:
    boundary = report.get("first_given_boundary") or {}
    burst = report.get("burst_id")
    n = int(boundary.get("nonempty_combinations_enumerated", 0) or 0)
    return f"""# NØ やさしい報告 — {burst}

## 今回、0からどこまで進んだ？

**NØの中では、0から1へ進んだとは判定していません。**

本当に何も物理的に与えないため、物・空間・時間・乱数・法則だけでなく、**「次へ進む」という仕組み自体を置いていない**からです。

## 順番に何をした？

1. NØ側の物理的な与え物が0個であることを確認しました。
2. 「次の状態」を1回も計算しませんでした。更新則や時間を置くと、それ自体が最初の与え物になるためです。
3. `something_observed=false` を記録しました。ただしこれは新しい物理測定ではなく、**何も生成しないnull-controlの構成値**です。
4. NØの外側で、最初に入り込みうる16種類の前提について **{n:,}通りを列挙**しました。これは{n:,}回の物理実験ではなく、「何を足したらNØではなくなるか」の境界地図です。

## 📸 画像は何を表す？

`nothing_latest.png` は物理世界の写真ではありません。16種類の前提を何個ずつ組み合わせたケースが何通りあるかを示した**メタな境界地図**です。可視化は物理データと分離しています。

## 次にできること

- **A. 最初の1個だけを一つずつ与える** — existence / 区別 / 関係 / 変化可能性などを単独で置き、どこから初めて「実験」が定義できるか比べる。
- **B. 「全てが起きうる0」N0-Pを別モデルとして作る** — ただし可能性構造を与えたモデルであり、Strict Nothingとは呼ばない。
- **C. R0をさらに削る** — 区別・関係・変化可能性のどれが本当に最低限必要か、ablationで壊す。

### 推奨

**まずAを優先**します。NØそのものをseed違いで水増しせず、「最初の一物を何にした時だけ何が可能になるか」を一つずつ比べる方が、完全な無との境界をいちばん正直に狭められます。

> 今回も「無から何かが生まれた／生まれない」を証明したわけではありません。分かったのは、何も定義しないままでは計算上の状態遷移を測れない、という境界です。
"""


def run_nothing_research(
    *, burst_id: str | None = None, persist: bool = True,
    boundary_names: tuple[str, ...] = FIRST_GIVEN_CANDIDATES,
    r0_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_burst = str(burst_id if burst_id is not None else _latest_burst_id())
    strict = strict_nothing_control()
    if strict["physical_layer"]["physical_givens"]:
        raise RuntimeError("NØ contamination: physical givens are not empty")
    if strict["result"]["something_observed"]:
        raise RuntimeError("NØ contamination: something appeared without a traceable added assumption")
    boundary = enumerate_first_given_boundary(boundary_names)
    paths = _archive_paths(resolved_burst)
    report = {
        "version": 3,
        "mode": "strict-nothing-genesis-meta-control",
        "burst_id": resolved_burst,
        "research_question": "本当に何も物理的に与えないとき、何かが生まれたと計算実験で言えるか。",
        "strict_trial_count": 1,
        "why_not_repeat_strict_trial_with_many_seeds": "seed・試行回数・サイズ・時間・乱数をNØ内部に入れた瞬間、それは『何もない』ではなくなるため。",
        "strict_nothing": strict,
        "all_things_possible_zero": possibility_zero_boundary(),
        "first_given_boundary": boundary,
        "comparison_to_R0": {
            "R0_is_downstream_of_NØ": True,
            "R0_adds": ["distinguishability", "relation", "change_possibility"],
            "R0_results_count_as_strict_nothing_results": False,
            "triggering_R0_metadata": _compact_r0_metadata(r0_metadata),
        },
        "claim_limits": {
            "proves_metaphysical_nothing_cannot_create_something": False,
            "proves_metaphysical_nothing_can_create_something": False,
            "computational_boundary_identified": True,
            "boundary_enumeration_is_physical_experiment": False,
            "if_future_strict_arm_reports_something": "treat_as_hidden_assumption_or_software_bug_until_traced",
        },
        "visualization": {
            "latest_path": "ai_lab/reports/easy/nothing_latest.png",
            "archive_path": str(paths["screenshot"].relative_to(_REPO)),
            "kind": "first-given-combination-count-boundary-map",
            "separated_from_physics_data": True,
            "physical_data_visualized": False,
            "changes_physical_result": False,
        },
        "evidence_package": {
            "technical_latest": "ai_lab/reports/easy/nothing_latest.json",
            "human_latest": "ai_lab/reports/easy/nothing_latest.md",
            "screenshot_latest": "ai_lab/reports/easy/nothing_latest.png",
            "immutable_archive_root": str(paths["root"].relative_to(_REPO)),
        },
        "technical_audit": _technical_audit(strict, boundary, boundary_names=boundary_names),
    }
    if not report["technical_audit"]["determinism"]["passed"]:
        raise RuntimeError("NØ meta-control determinism audit failed")
    if persist:
        human = _human_markdown(report)
        png = _boundary_png(boundary)
        _write(_REPORT, report)
        _HUMAN.parent.mkdir(parents=True, exist_ok=True)
        _HUMAN.write_text(human)
        _SCREENSHOT.write_bytes(png)
        _write(paths["report"], report)
        paths["human"].write_text(human)
        paths["screenshot"].write_bytes(png)
    return report


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Aeterna strict Nothing Genesis (NØ) control")
    ap.add_argument("--burst-id", default=None, help="standalone fallback defaults to tracked easy/latest burst id")
    ap.add_argument("--no-record", action="store_true", help="write only under runtime/dry-run/latest via dry-run redirect")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    # Resolve repository fallback before activating scratch redirection; otherwise stale scratch latest
    # evidence from a prior dry-run could lend the wrong burst id to this standalone invocation.
    resolved_burst = str(a.burst_id) if a.burst_id is not None else _latest_burst_id()
    if a.no_record:
        dry_run.activate()
    r = run_nothing_research(burst_id=resolved_burst, persist=True)
    b = r["first_given_boundary"]
    print(f"=== Nothing Genesis NØ: {r['burst_id']} ===")
    print("  strict physical givens=0; transition defined=False; something observed=False (null-control construction)")
    print(f"  meta boundary combinations enumerated={b['nonempty_combinations_enumerated']}")
    print("  N0-P ('all things can happen') is boundary-only, not injected into strict nothing")
    print("  screenshot=ai_lab/reports/easy/nothing_latest.png (meta visualization, not physics data)")
    print("  human=ai_lab/reports/easy/nothing_latest.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())