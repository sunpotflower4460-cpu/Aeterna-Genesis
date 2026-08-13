"""Record the numerical/software environment that produced a research burst.

Aeterna's requirements intentionally allow compatible package ranges, so the repository source alone is
not enough to reconstruct the exact numerical environment of an old burst.  This report captures the
actual interpreter, installed distribution versions, numerical-thread settings, platform and hashes of the
requirements/workflow contract.

The fingerprint is provenance only.  Package versions, BLAS configuration or a matching environment do not
make a scientific result true; they make it easier to reproduce and diagnose it.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_EASY = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"
_OUTPUT = _REPO / "ai_lab" / "reports" / "easy" / "environment_latest.json"
_REQUIREMENTS = _REPO / "requirements.txt"
_DREAM_WORKFLOW = _REPO / ".github" / "workflows" / "dream-loop.yml"

_NUMERICAL_ENV_NAMES = (
    "PYTHONHASHSEED",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _installed_distributions() -> dict[str, str]:
    rows: dict[str, str] = {}
    for dist in importlib.metadata.distributions():
        try:
            name = str(dist.metadata.get("Name") or "").strip()
            version = str(dist.version or "").strip()
        except Exception:
            continue
        if name:
            rows[name.lower()] = version
    return dict(sorted(rows.items()))


def _numpy_configuration() -> dict[str, Any]:
    try:
        import numpy as np
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    stream = io.StringIO()
    try:
        with contextlib.redirect_stdout(stream):
            np.show_config()
        text = stream.getvalue().strip()
    except Exception as exc:
        text = f"show_config failed: {type(exc).__name__}: {exc}"
    return {
        "available": True,
        "version": str(np.__version__),
        "show_config": text,
    }


def build_fingerprint(*, burst_id: str | None = None) -> dict[str, Any]:
    easy = _read_json(_EASY, {})
    burst = str(burst_id or easy.get("burst_id") or "")
    if not burst:
        raise RuntimeError("cannot record research environment without a burst_id")
    packages = _installed_distributions()
    return {
        "version": 1,
        "mode": "research-execution-environment-fingerprint",
        "burst_id": burst,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": {
            "version": sys.version,
            "version_info": list(sys.version_info[:5]),
            "implementation": platform.python_implementation(),
            "executable_name": Path(sys.executable).name,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_compiler": platform.python_compiler(),
            "cpu_count": os.cpu_count(),
        },
        "numerical_thread_environment": {
            name: os.environ.get(name) for name in _NUMERICAL_ENV_NAMES
        },
        "installed_distributions": packages,
        "core_versions": {
            name: packages.get(name)
            for name in ("numpy", "scipy", "pyyaml", "jsonschema", "pytest")
        },
        "numpy_configuration": _numpy_configuration(),
        "contracts": {
            "requirements_txt_sha256": _sha256(_REQUIREMENTS),
            "dream_loop_workflow_sha256": _sha256(_DREAM_WORKFLOW),
        },
        "github_execution": {
            "sha": os.environ.get("GITHUB_SHA"),
            "ref": os.environ.get("GITHUB_REF"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_number": os.environ.get("GITHUB_RUN_NUMBER"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "runner_os": os.environ.get("RUNNER_OS"),
            "runner_arch": os.environ.get("RUNNER_ARCH"),
        },
        "semantics": {
            "matching_environment_proves_scientific_claim": False,
            "environment_fingerprint_is_physical_observable": False,
            "captures_secrets": False,
            "full_installed_distribution_versions_recorded": True,
            "requirements_ranges_alone_are_exact_reproduction_lock": False,
        },
        "integrity": {
            "changes_physics": False,
            "changes_initial_conditions": False,
            "changes_scientific_truth_gate": False,
            "promotes_rooms": False,
            "changes_official_levels": False,
        },
    }


def run(*, burst_id: str | None = None, persist: bool = True) -> dict[str, Any]:
    report = build_fingerprint(burst_id=burst_id)
    if persist:
        _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        _OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Record exact software/numerical environment for a research burst")
    p.add_argument("--burst-id", default=None)
    p.add_argument("--no-record", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run(burst_id=args.burst_id, persist=not args.no_record)
    print(
        f"Research Environment: burst={report.get('burst_id')} "
        f"python={report.get('python', {}).get('version_info', [])[:3]} "
        f"numpy={report.get('core_versions', {}).get('numpy')} "
        f"scipy={report.get('core_versions', {}).get('scipy')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
