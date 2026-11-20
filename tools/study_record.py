"""Check a study's declared inputs, planned cases and retained evidence. Read-only.

    python -m tools.study_record path/to/PLAN.json [path/to/record.json]
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess


def _unique_object(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_object(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(obj, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return obj


def _local_file(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError(f"expected a relative file inside {root}: {name!r}")
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"missing file or outside {root}: {name}")
    return path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_plan(path):
    plan = read_object(path)
    if type(plan.get("version")) is not int or plan["version"] != 1:
        raise ValueError("unsupported study plan version")
    for field in ("question", "prior_access", "independent_unit", "inputs", "measurement", "alternatives", "stopping"):
        if not isinstance(plan.get(field), str) or not plan[field].strip():
            raise ValueError(f"missing plan text: {field}")
    files, cases = plan.get("tracked_inputs"), plan.get("cases")
    if not isinstance(files, list) or not files or not all(isinstance(f, str) and f for f in files):
        raise ValueError("tracked_inputs must list the sources of the calculation")
    if not isinstance(cases, dict) or not cases or not all(k.strip() and isinstance(v, dict) for k, v in cases.items()):
        raise ValueError("cases must name each planned condition")
    return plan


def verify_registration(plan_path, plan, commit):
    """Check these bytes against a Git commit. Prior access is disclosed separately."""
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise ValueError("registration_commit must be a full Git commit ID")
    path = Path(plan_path).resolve()
    root = Path(subprocess.check_output(["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
                                        text=True).strip()).resolve()
    kind = subprocess.check_output(["git", "-C", str(root), "cat-file", "-t", commit], text=True).strip()
    if kind != "commit":
        raise ValueError("registration_commit must identify a commit")
    for name in [str(path.relative_to(root)), *plan["tracked_inputs"]]:
        source = _local_file(root, name)
        tree_id = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--verify",
                                           f"{commit}:{name}"], text=True).strip()
        current_id = subprocess.check_output(["git", "-C", str(root), "hash-object", "--no-filters", str(source)],
                                             text=True).strip()
        if tree_id != current_id:
            raise ValueError(f"changed since registration: {name}")


def check_record(plan_path, record_path):
    plan, record = load_plan(plan_path), read_object(record_path)
    verify_registration(plan_path, plan, record.get("registration_commit"))
    cases = record.get("cases")
    if not isinstance(cases, dict) or cases.keys() != plan["cases"].keys():
        raise ValueError("reported cases differ from the plan")
    root = Path(record_path).resolve().parent
    counts, checked = Counter(), {}
    for name, attempts in cases.items():
        if not isinstance(attempts, list) or not attempts:
            raise ValueError(f"{name}: account for every planned case")
        for attempt in attempts:
            status = attempt.get("status") if isinstance(attempt, dict) else None
            if status not in ("completed", "failed", "stopped", "running", "not_run"):
                raise ValueError(f"{name}: unknown attempt status")
            files = attempt.get("artifacts", {})
            if not isinstance(files, dict) or (status == "completed" and not files):
                raise ValueError(f"{name}: completed attempts need retained evidence")
            reason = attempt.get("reason")
            if status != "completed" and (not isinstance(reason, str) or not reason.strip()):
                raise ValueError(f"{name}: record why the attempt is {status}")
            for filename, expected in files.items():
                artifact = _local_file(root, filename)
                if artifact not in checked:
                    checked[artifact] = sha256(artifact)
                if expected != checked[artifact]:
                    raise ValueError(f"{name}: SHA-256 mismatch for {filename}")
            counts[status] += 1
    return {"planned_cases": len(cases), "attempts_by_status": dict(counts), "verified_files": len(checked)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("record", type=Path, nargs="?")
    args = parser.parse_args()
    try:
        if args.record is None:
            result = {"planned_cases": len(load_plan(args.plan)["cases"])}
        else:
            result = check_record(args.plan, args.record)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"study record: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
