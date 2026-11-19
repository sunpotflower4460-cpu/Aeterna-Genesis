"""Independently remeasure every archived v01 3D checkpoint."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
from scipy.ndimage import uniform_filter

from run import HERE, json_text, read_json, sha256

sys.path.insert(0, str(HERE.parents[2]))
from observe import THRESHOLDS, periodic_components

REGISTRATION = HERE / "LEGACY_CHECKPOINT_PLAN.json"


def verify(raw, reference, path):
    if len(raw) != reference["bytes"] or hashlib.sha256(raw).hexdigest() != reference["sha256"]:
        raise ValueError(f"Legacy file failed SHA-256 verification: {path}")
    return raw


def remeasure(manifest_path: Path):
    manifest = read_json(manifest_path)
    archive_path = manifest_path.parent / "checkpoints.zip"
    if sha256(archive_path) != manifest["checkpoint_archive_sha256"]:
        raise ValueError("Changed legacy checkpoint archive")

    records = []
    with zipfile.ZipFile(archive_path) as bundle:
        for run in manifest["runs"]:
            if run["dimension"] != 3:
                continue
            history = run["path"]
            raw_path = manifest_path.parent / "histories" / history
            recipe = json.loads(verify(
                (raw_path / "recipe.json").read_bytes(), run["files"]["recipe.json"], f"{history}/recipe",
            ))
            summary = json.loads(verify(
                (raw_path / "summary.json").read_bytes(), run["files"]["summary.json"], f"{history}/summary",
            ))
            for frame in summary["frames"]:
                prefix = f"state-{frame['sample']}"
                cells = None
                for kind in ("cells", "positions", "conformers", "displacements"):
                    name = f"{prefix}-{kind}.bin"
                    member = f"{history}/{name}"
                    raw = verify(bundle.read(member), run["files"][name], member)
                    if kind == "cells":
                        cells = np.frombuffer(raw, dtype=np.uint8).reshape((recipe["N"],) * 3, order="F")
                rho = uniform_filter((cells > 0).astype(float), size=4, mode="wrap")
                regions = {}
                for threshold in THRESHOLDS:
                    key = str(threshold)
                    measurement = periodic_components(rho > threshold)
                    original = frame["regions"][key]
                    if (
                        measurement["count"] != original["count"]
                        or measurement["largest_volumes"] != original["largest_volumes"]
                    ):
                        raise ValueError(f"Legacy periodic component mismatch at {history}/{prefix}, threshold {key}")
                    regions[key] = measurement
                records.append({
                    "history": history, "time": frame["time"], "sample": frame["sample"],
                    "N": recipe["N"], "T": recipe["T"], "regions": regions,
                })
    return records, manifest["checkpoint_archive_sha256"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    protocol = read_json(REGISTRATION)
    path = (HERE / protocol["source"]).resolve()
    records, archive_digest = remeasure(path)
    history_count = len({record["history"] for record in records})
    if history_count != protocol["histories"]:
        raise ValueError(f"Unexpected legacy history count: {history_count}")
    summary = {
        "history_count": history_count,
        "frame_count": len(records),
        "verified_periodic_counts": len(records) * len(THRESHOLDS),
        "legacy_checkpoint_sha256": archive_digest,
        "registration_sha256": sha256(REGISTRATION),
        "thresholds": {},
        "final_volume_controls": [record for record in records
                                  if record["history"].startswith("volume/") and record["time"] == record["T"]],
    }
    for threshold in THRESHOLDS:
        key = str(threshold)
        regions = [record["regions"][key] for record in records]
        summary["thresholds"][key] = {
            "frames_with_cut_open_fragmentation": sum(r["cut_open_count"] != r["count"] for r in regions),
            "frames_with_winding": sum(r["winding_component_count"] > 0 for r in regions),
            "frames_winding_in_at_least_one_axis_by_axis": [
                sum(r["winding_axes_any"][axis] for r in regions) for axis in range(3)
            ],
        }
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "legacy-summary.json").write_text(json_text(summary), encoding="utf-8")
    (args.out / "legacy-frames.json.gz").write_bytes(gzip.compress(json_text(records).encode(), mtime=0))
    print(f"Verified {summary['verified_periodic_counts']} measurements over {history_count} legacy histories")


if __name__ == "__main__":
    main()
