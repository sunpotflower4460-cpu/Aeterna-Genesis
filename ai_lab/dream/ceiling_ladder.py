"""Ceiling ladder: is the Level-2 wall physics, or the screening window?

Across 156,804 recorded trials the search has never reported a level above 2, while the hourly screen
always runs at the ``--quick`` window of a 48-cell grid for 260 steps. Level 2 is "localised
structure, defects, vortices"; Level 3 is "spontaneous motion, interaction, circulation". A structure
has to form *and then be seen moving*, so a flat ceiling is exactly what a too-short window would also
produce. Those two explanations have very different consequences and cannot be told apart by running
more trials at the same window.

This re-measures already-recorded candidates through progressively wider windows. It is a
re-measurement, not a deeper model:

* the initial condition family, the knobs and the seed are the recorded ones, unchanged,
* every rung starts again from t=0 -- no rung continues another,
* only (grid edge, steps, snapshots) change, and those are numerical regulators, not physics,
* no Level N+1 mechanism is added to reach past Level N (AGENTS.md discipline 2).

Verdicts are deliberately asymmetric. Seeing a higher level at a wider window *proves* the recorded
ceiling was the window. Not seeing one proves only that the ceiling survived this ladder -- never
that a physical ceiling has been established.
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_lab import lab
from ai_lab.dream import dry_run
from genesis.diagnostics import measures

_REPO = Path(__file__).resolve().parents[2]
_LEDGER = _REPO / "ai_lab" / "discoveries" / "ledger.json"
_OUT = _REPO / "ai_lab" / "reports" / "ceiling"

# (grid edge, steps, snapshots). Rung 0 reproduces the production screen so every ladder carries its
# own control instead of trusting the historical number.
DEFAULT_LADDER: tuple[tuple[int, int, int], ...] = (
    (48, 260, 10),  # production --quick screen
    (48, 1040, 16),  # same grid, 4x the time
    (96, 800, 16),  # 2x the grid, 3x the time
    (96, 2400, 20),  # widest rung
)


def instrument_max_level() -> int:
    """Highest level the 2D screen's assessor can express at all -- measured, not assumed.

    A trajectory more extreme than any real run is fed to the same assessor the search uses. Whatever
    it returns is the instrument's ceiling: the search cannot report a level above it no matter what
    the field does, so a recorded ceiling at that value says nothing about physics.
    """
    extreme = [{"mean_amp": 1e-6, "sk_prom": 0.0, "defects": 0}] + [
        {"mean_amp": 1e6, "sk_prom": 1e6, "defects": 4096} for _ in range(19)
    ]
    level, _, _ = measures.assess_level(extreme)
    return int(level)


def _rung_name(window: tuple[int, int, int]) -> str:
    return f"edge{window[0]}-steps{window[1]}"


def load_candidates(*, top: int, ledger_path: Path | None = None) -> list[dict[str, Any]]:
    """Take the highest-scoring recorded screens that have a reproducible IC.

    Selection uses the recorded score only to spend a limited budget where structure already exists.
    It does not decide any verdict; every selected candidate is reported, including the ones that do
    not move.
    """
    path = ledger_path or _LEDGER
    doc = json.loads(path.read_text()) if path.exists() else {}
    rows = [
        r for r in (doc.get("search_discoveries") or [])
        if r.get("family") and isinstance(r.get("knobs"), dict) and r.get("seed") is not None
        and r.get("score") is not None
    ]
    rows.sort(key=lambda r: float(r.get("score") or 0.0), reverse=True)
    seen: set[tuple[Any, ...]] = set()
    picked: list[dict[str, Any]] = []
    for row in rows:
        key = (row["family"], int(row["seed"]), json.dumps(row["knobs"], sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        picked.append({
            "family": str(row["family"]),
            "knobs": dict(row["knobs"]),
            "seed": int(row["seed"]),
            "recorded_level": int(row.get("reached_level") or 0),
            "recorded_score": float(row.get("score") or 0.0),
        })
        if len(picked) >= max(0, top):
            break
    return picked


def _run_rung(task: dict[str, Any]) -> dict[str, Any]:
    window = tuple(task["window"])
    result = lab._screen_ic(task["family"], task["knobs"], int(task["seed"]), window=window)
    return {
        "candidate": task["candidate"],
        "rung": _rung_name(window),
        "window": {"edge": window[0], "steps": window[1], "snapshots": window[2]},
        "reached_level": result.get("reached_level"),
        "score": result.get("score"),
        "status": result.get("status"),
        "measured_by": result.get("measured_by") or {},
    }


def run_ladder(
    *, top: int = 24, ladder: tuple[tuple[int, int, int], ...] = DEFAULT_LADDER,
    workers: int = 4, ledger_path: Path | None = None,
) -> dict[str, Any]:
    candidates = load_candidates(top=top, ledger_path=ledger_path)
    tasks = [
        {"candidate": i, "family": c["family"], "knobs": c["knobs"], "seed": c["seed"], "window": w}
        for i, c in enumerate(candidates) for w in ladder
    ]
    if workers <= 1 or len(tasks) <= 1:
        rows = [_run_rung(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(_run_rung, tasks))

    by_candidate: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_candidate.setdefault(int(row["candidate"]), []).append(row)

    per_candidate = []
    lifted = 0
    for i, cand in enumerate(candidates):
        runs = sorted(by_candidate.get(i, []), key=lambda r: (r["window"]["edge"], r["window"]["steps"]))
        levels = [int(r["reached_level"] or 0) for r in runs if r.get("status") != "unstable"]
        baseline = levels[0] if levels else 0
        best = max(levels) if levels else 0
        moved = best > baseline
        lifted += int(moved)
        per_candidate.append({
            **cand,
            "baseline_level_at_production_window": baseline,
            "best_level_across_ladder": best,
            "level_rose_with_window": moved,
            "unstable_rungs": [r["rung"] for r in runs if r.get("status") == "unstable"],
            "rungs": [
                {"rung": r["rung"], **r["window"], "reached_level": r["reached_level"],
                 "score": r["score"], "status": r["status"]}
                for r in runs
            ],
        })

    best_overall = max([c["best_level_across_ladder"] for c in per_candidate] or [0])
    baseline_overall = max([c["baseline_level_at_production_window"] for c in per_candidate] or [0])
    instrument_max = instrument_max_level()

    # If the best result already sits at the highest value the assessor can express, deeper behavior
    # is unreportable by this instrument. That fact is not a physical result.
    unreportable = bool(best_overall >= instrument_max)

    if best_overall > baseline_overall:
        verdict = "window_limited"
        plain = (
            "広い窓で見ると、これまでの記録より深い段階が現れました。"
            "つまりこれまでの上限は、自然の天井ではなく観測の窓の狭さでした。"
        )
    elif unreportable:
        verdict = "instrument_limited"
        plain = (
            "この探索が使っている測定器は、そもそも今の段階より深い段階を表現できません。"
            "記録された上限は自然の天井でも窓の狭さでもなく、測定器の上限です。"
            "深い段階を確かめるには、まず測り方を増やす必要があります。"
        )
    else:
        verdict = "ceiling_survived_this_ladder"
        plain = (
            "窓を広げても深い段階は現れませんでした。"
            "ただしこれは、この梯子の範囲で上限が残ったという意味であり、自然の天井が証明されたわけではありません。"
        )

    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "question": "記録済みの上限は物理の天井か、それとも観測窓の天井か。",
        "method": "同じ初期条件・同じ法則・同じ種を、観測窓だけ広げて t=0 から測り直す。",
        "ladder": [{"rung": _rung_name(w), "edge": w[0], "steps": w[1], "snapshots": w[2]} for w in ladder],
        "candidates_tested": len(candidates),
        "baseline_best_level": baseline_overall,
        "ladder_best_level": best_overall,
        "candidates_whose_level_rose": lifted,
        "instrument_max_expressible_level": instrument_max,
        "recorded_ceiling_equals_instrument_ceiling": unreportable,
        "deeper_levels_are_unreportable_by_this_instrument": unreportable,
        "verdict": verdict,
        "plain": plain,
        "per_candidate": per_candidate,
        "claim_tier": "measured",
        "honesty": {
            "window_is_a_numerical_regulator_not_physics": True,
            "initial_conditions_were_changed": False,
            "law_was_changed": False,
            "a_rung_continues_a_previous_rung": False,
            "level_N_plus_1_mechanism_was_added": False,
            "flat_ladder_proves_a_physical_ceiling": False,
            "a_ceiling_at_the_instrument_maximum_is_a_physical_result": False,
            "changes_official_level_or_room_promotion": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 天井の切り分け（観測窓の梯子）",
        "",
        "## 何を確かめたか",
        str(report.get("question") or ""),
        "",
        "## やり方",
        str(report.get("method") or ""),
        "",
        "## 結果",
        str(report.get("plain") or ""),
        "",
        f"- 記録どおりの窓での最良段階: {report.get('baseline_best_level')}",
        f"- 窓を広げたときの最良段階: {report.get('ladder_best_level')}",
        f"- 段階が上がった候補: {report.get('candidates_whose_level_rose')} / {report.get('candidates_tested')}",
        f"- いま使っている測定器が表現できる最も深い段階: {report.get('instrument_max_expressible_level')}",
        "",
        "## 言っていないこと",
        "- 窓の広さは計算上の設定であって、物理の性質ではありません。",
        "- 梯子が平らでも、それは自然の天井の証明ではありません。",
        "- この測り直しは公式段階や Room の昇格を変えません。",
    ]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tell a physical ceiling apart from a screening-window ceiling")
    ap.add_argument("--top", type=int, default=24, help="recorded candidates to re-measure")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--no-record", action="store_true", help="write to runtime/dry-run/ instead of the repo")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if a.no_record:
        dry_run.activate()
    report = run_ladder(top=max(1, a.top), workers=max(1, a.workers))
    _OUT.mkdir(parents=True, exist_ok=True)
    (_OUT / "latest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    (_OUT / "latest.md").write_text(render_markdown(report))
    print(f"=== ceiling ladder: {report['verdict']} ===")
    print(f"  candidates={report['candidates_tested']} baseline_best={report['baseline_best_level']} "
          f"ladder_best={report['ladder_best_level']} rose={report['candidates_whose_level_rose']}")
    print(f"  instrument can express up to level {report['instrument_max_expressible_level']}")
    print(f"  {report['plain']}")
    print("  NOTE: the window is a numerical regulator; a flat ladder does not prove a physical ceiling.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
