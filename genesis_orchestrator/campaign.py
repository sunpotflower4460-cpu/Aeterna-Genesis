"""Campaign validation and deterministic job compilation."""

from __future__ import annotations

import copy
import itertools
import json
import re
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from genesis.runners import runner

from . import db

ALLOWED_STAGES = ("2d-screen", "local-3d", "coarse-global-3d", "full-3d")
APPLIED_KNOBS = ("noise_amplitude", "quench_duration")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_schema(root: Path) -> dict[str, Any]:
    return json.loads((root / "schemas" / "campaign.schema.json").read_text())


def load_campaign(path: str | Path, root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    source = Path(path)
    doc = yaml.safe_load(source.read_text())
    Draft202012Validator(_load_schema(root)).validate(doc)
    _semantic_validate(doc, root)
    return doc


def _semantic_validate(doc: dict[str, Any], root: Path) -> None:
    campaign_id = doc["campaign_id"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", campaign_id):
        raise ValueError("campaign_id must be lowercase kebab-case (3..64 chars)")
    model = doc.get("model", runner._DEMO_GENESIS["model"])
    if model not in runner.MODELS:
        raise ValueError(f"model {model!r} is not supported by the common runner")
    for hyp in doc["hypotheses"]:
        stages = hyp.get("stages", doc.get("stages", list(ALLOWED_STAGES)))
        if not stages or stages[0] != "2d-screen":
            raise ValueError(f"{hyp['id']}: pipeline must start with 2d-screen")
        if any(s not in ALLOWED_STAGES for s in stages):
            raise ValueError(f"{hyp['id']}: unsupported stage in {stages}")
        if list(stages) != sorted(stages, key=ALLOWED_STAGES.index):
            raise ValueError(f"{hyp['id']}: stages must follow 2D -> local 3D -> coarse 3D -> full 3D")
        for overrides in _variant_overrides(hyp):
            _validate_overrides(overrides, root)


def _validate_overrides(overrides: dict[str, float], root: Path) -> None:
    unknown = sorted(set(overrides) - set(APPLIED_KNOBS))
    if unknown:
        raise ValueError(
            "unsupported knob(s): %s. The common runner currently applies only %s; "
            "rejecting unapplied knobs avoids recording a condition the physics did not use."
            % (", ".join(unknown), ", ".join(APPLIED_KNOBS))
        )
    ranges = yaml.safe_load((root / "genesis" / "registry" / "param_ranges.yaml").read_text())["search_space"]
    if "noise_amplitude" in overrides:
        spec = ranges["initial_state"]["noise_amplitude"]
        value = float(overrides["noise_amplitude"])
        if not float(spec["min"]) <= value <= float(spec["max"]):
            raise ValueError(f"noise_amplitude={value} is outside [{spec['min']}, {spec['max']}]")
    if "quench_duration" in overrides:
        value = float(overrides["quench_duration"])
        if not 0.0 < value <= 40.0:
            raise ValueError("quench_duration must be in (0, 40]")


def _variant_overrides(hypothesis: dict[str, Any]) -> list[dict[str, float]]:
    search = hypothesis["search"]
    variants: list[dict[str, float]] = []
    for item in search.get("variants", []):
        variants.append({k: float(v) for k, v in item["overrides"].items()})
    grid = search.get("grid") or {}
    if grid:
        keys = sorted(grid)
        for values in itertools.product(*(grid[k] for k in keys)):
            variants.append({k: float(v) for k, v in zip(keys, values)})
    if not variants:
        raise ValueError(f"{hypothesis['id']}: search must contain variants or grid")
    seen: set[str] = set()
    unique: list[dict[str, float]] = []
    for variant in variants:
        key = json.dumps(variant, sort_keys=True, separators=(",", ":"))
        if key not in seen:
            unique.append(variant)
            seen.add(key)
    return unique


def _apply_overrides(base: dict[str, Any], overrides: dict[str, float], seed: int) -> dict[str, Any]:
    genesis = copy.deepcopy(base)
    genesis["seed"] = int(seed)
    genesis.setdefault("initial_state", {})
    genesis.setdefault("protocol", {}).setdefault("quench", {})
    if "noise_amplitude" in overrides:
        genesis["initial_state"]["noise_amplitude"] = float(overrides["noise_amplitude"])
    if "quench_duration" in overrides:
        genesis["protocol"]["quench"]["duration"] = float(overrides["quench_duration"])
    return genesis


def compile_campaign(doc: dict[str, Any], source_path: str | None = None) -> list[dict[str, Any]]:
    """Compile only the first stage of every trial.

    Later 3D jobs are created by the worker only after the preceding measured stage survives.
    """
    campaign_id = doc["campaign_id"]
    parent_room = doc.get("parent_room", "room-g001-a")
    model = doc.get("model", runner._DEMO_GENESIS["model"])
    default_stages = doc.get("stages", list(ALLOWED_STAGES))
    default_approvals = doc.get("approval_required", ["coarse-global-3d", "full-3d"])
    default_quick = bool(doc.get("quick", False))
    default_min_level = int(doc.get("min_reached_level", 1))
    base = copy.deepcopy(runner._DEMO_GENESIS)
    base["model"] = model

    jobs: list[dict[str, Any]] = []
    for hypothesis in doc["hypotheses"]:
        variants = _variant_overrides(hypothesis)
        seeds = [int(s) for s in hypothesis.get("seeds", doc.get("seeds", [0]))]
        stages = list(hypothesis.get("stages", default_stages))
        approvals = list(hypothesis.get("approval_required", default_approvals))
        quick = bool(hypothesis.get("quick", default_quick))
        min_level = int(hypothesis.get("min_reached_level", default_min_level))
        for variant_index, overrides in enumerate(variants):
            trial_id = f"{hypothesis['id']}-v{variant_index:03d}"
            for seed in seeds:
                genesis = _apply_overrides(base, overrides, seed)
                job_id = db.make_job_id(campaign_id, trial_id, stages[0], seed)
                jobs.append(
                    {
                        "job_id": job_id,
                        "campaign_id": campaign_id,
                        "hypothesis_id": hypothesis["id"],
                        "trial_id": trial_id,
                        "parent_room": parent_room,
                        "model": model,
                        "stage": stages[0],
                        "stage_index": 0,
                        "pipeline": stages,
                        "approval_stages": approvals,
                        "seed": seed,
                        "quick": quick,
                        "genesis": genesis,
                        "overrides": overrides,
                        "min_reached_level": min_level,
                        "status": "queued",
                        "approved": True,
                        "priority": int(hypothesis.get("priority", 100)),
                    }
                )
    return jobs


def submit(path: str | Path, database: str | Path, root: Path | None = None) -> tuple[dict[str, Any], int]:
    root = root or repo_root()
    doc = load_campaign(path, root=root)
    db.init_db(database)
    db.add_campaign(
        database,
        campaign_id=doc["campaign_id"],
        title=doc["title"],
        document=doc,
        source_path=str(path),
    )
    inserted = db.add_jobs(database, compile_campaign(doc, source_path=str(path)))
    return doc, inserted
