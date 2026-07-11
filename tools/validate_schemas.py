#!/usr/bin/env python3
"""CI-B: Schema and Registry validation for the Genesis migration.

Checks (setup PR2 scope):
  1. Every schemas/*.json is a well-formed JSON Schema (draft 2020-12).
  2. Every genesis/registry/{models,solvers,diagnostics,invariants}.yaml validates
     against schemas/registry.schema.json.
  3. No duplicate entry ids within a registry file.
  4. Every related_experiments reference points at an existing experiments/e0xx/ directory
     (broken-reference guard).
  5. param_ranges.yaml is valid YAML with the required top-level keys.

Later PRs extend this (experiment.yaml against experiment.schema.json in PR3; room/run/emergence in PR6).

Exit nonzero on any violation. Dependency: jsonschema, PyYAML (see requirements.txt).
"""

import json
import os
import sys

import yaml
from jsonschema import Draft202012Validator

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SCHEMAS = os.path.join(_REPO, "schemas")
_REGISTRY = os.path.join(_REPO, "genesis", "registry")

_REGISTRY_FILES = {
    "models.yaml": "models",
    "solvers.yaml": "solvers",
    "diagnostics.yaml": "diagnostics",
    "invariants.yaml": "invariants",
}


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    errors = []
    info = []

    # 1. All schemas are well-formed JSON Schema.
    schema_files = sorted(f for f in os.listdir(_SCHEMAS) if f.endswith(".json"))
    if not schema_files:
        errors.append("no schemas/*.json found")
    for fn in schema_files:
        path = os.path.join(_SCHEMAS, fn)
        try:
            schema = _load_json(path)
            Draft202012Validator.check_schema(schema)
            info.append("schema OK: schemas/%s" % fn)
        except Exception as e:  # noqa: BLE001
            errors.append("invalid schema schemas/%s: %s" % (fn, e))

    # 2-4. Registry files validate against registry.schema.json; ids unique; refs exist.
    reg_schema_path = os.path.join(_SCHEMAS, "registry.schema.json")
    reg_validator = None
    if os.path.exists(reg_schema_path):
        try:
            reg_validator = Draft202012Validator(_load_json(reg_schema_path))
        except Exception as e:  # noqa: BLE001
            errors.append("registry.schema.json unusable: %s" % e)

    for fn, kind in _REGISTRY_FILES.items():
        path = os.path.join(_REGISTRY, fn)
        if not os.path.exists(path):
            errors.append("missing registry file genesis/registry/%s" % fn)
            continue
        try:
            doc = _load_yaml(path)
        except Exception as e:  # noqa: BLE001
            errors.append("invalid YAML genesis/registry/%s: %s" % (fn, e))
            continue
        if doc.get("kind") != kind:
            errors.append("genesis/registry/%s: kind must be '%s' (got %r)" % (fn, kind, doc.get("kind")))
        if reg_validator is not None:
            for err in reg_validator.iter_errors(doc):
                errors.append("genesis/registry/%s: %s at %s"
                              % (fn, err.message, list(err.absolute_path)))
        # unique ids
        ids = [e.get("id") for e in doc.get("entries", [])]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            errors.append("genesis/registry/%s: duplicate entry ids %s" % (fn, dupes))
        # related_experiments references exist
        for e in doc.get("entries", []):
            for ref in e.get("related_experiments", []):
                matches = [d for d in os.listdir(os.path.join(_REPO, "experiments"))
                           if d.startswith(ref + "_")] if os.path.isdir(os.path.join(_REPO, "experiments")) else []
                if not matches:
                    errors.append("genesis/registry/%s: entry %r references unknown experiment %s"
                                  % (fn, e.get("id"), ref))
        info.append("registry OK: genesis/registry/%s (%d entries)" % (fn, len(doc.get("entries", []))))

    # 5. param_ranges.yaml sanity.
    pr_path = os.path.join(_REGISTRY, "param_ranges.yaml")
    if not os.path.exists(pr_path):
        errors.append("missing genesis/registry/param_ranges.yaml")
    else:
        try:
            pr = _load_yaml(pr_path)
            for key in ("search_space", "mutation_types", "forbidden_to_change"):
                if key not in pr:
                    errors.append("param_ranges.yaml: missing top-level key %r" % key)
            info.append("param_ranges OK")
        except Exception as e:  # noqa: BLE001
            errors.append("invalid param_ranges.yaml: %s" % e)

    # 6. Every experiments/e0xx/experiment.yaml validates against experiment.schema.json (PR3),
    #    its id matches the directory prefix, and the 8th-audit rule holds
    #    (target_encoded=true => primary role must NOT be E or V).
    exp_schema_path = os.path.join(_SCHEMAS, "experiment.schema.json")
    exp_dir = os.path.join(_REPO, "experiments")
    n_exp = 0
    if os.path.exists(exp_schema_path) and os.path.isdir(exp_dir):
        try:
            exp_validator = Draft202012Validator(_load_json(exp_schema_path))
        except Exception as e:  # noqa: BLE001
            exp_validator = None
            errors.append("experiment.schema.json unusable: %s" % e)
        for dirname in sorted(d for d in os.listdir(exp_dir) if d.startswith("e0")):
            ypath = os.path.join(exp_dir, dirname, "experiment.yaml")
            if not os.path.exists(ypath):
                errors.append("missing experiments/%s/experiment.yaml" % dirname)
                continue
            try:
                doc = _load_yaml(ypath)
            except Exception as e:  # noqa: BLE001
                errors.append("invalid YAML experiments/%s/experiment.yaml: %s" % (dirname, e))
                continue
            if exp_validator is not None:
                for err in exp_validator.iter_errors(doc):
                    errors.append("experiments/%s/experiment.yaml: %s at %s"
                                  % (dirname, err.message, list(err.absolute_path)))
            if doc.get("id") != dirname.split("_")[0]:
                errors.append("experiments/%s/experiment.yaml: id %r must match dir prefix"
                              % (dirname, doc.get("id")))
            primary = (doc.get("role") or {}).get("primary")
            if doc.get("target_encoded") and primary in ("E", "V"):
                errors.append("experiments/%s/experiment.yaml: 8th-audit violation "
                              "(target_encoded=true but primary role is %s; must be S/F/Q)"
                              % (dirname, primary))
            n_exp += 1
        info.append("experiment.yaml OK: %d validated (schema + id match + 8th-audit)" % n_exp)

    # 7. Every rooms/official/*/ Genesis Room validates against the room/genesis/emergence/
    #    dimension-transfer/render schemas, and each run manifest/emergence too (PR6).
    rooms_dir = os.path.join(_REPO, "rooms", "official")
    n_rooms = 0
    _room_schemas = {"genesis.yaml": "genesis.schema.json", "room.yaml": "room.schema.json",
                     "dimension-transfer.yaml": "dimension-transfer.schema.json",
                     "render.yaml": "render.schema.json"}
    if os.path.isdir(rooms_dir):
        validators = {}
        for sfile in set(list(_room_schemas.values()) + ["emergence.schema.json", "run.schema.json",
                                                          "field-index.schema.json", "render-manifest.schema.json"]):
            try:
                validators[sfile] = Draft202012Validator(_load_json(os.path.join(_SCHEMAS, sfile)))
            except Exception as e:  # noqa: BLE001
                errors.append("%s unusable: %s" % (sfile, e))
        for room in sorted(d for d in os.listdir(rooms_dir) if os.path.isdir(os.path.join(rooms_dir, d))):
            rdir = os.path.join(rooms_dir, room)
            for fn, sfile in _room_schemas.items():
                fpath = os.path.join(rdir, fn)
                if not os.path.exists(fpath):
                    errors.append("missing rooms/official/%s/%s" % (room, fn))
                    continue
                v = validators.get(sfile)
                if v is not None:
                    for err in v.iter_errors(_load_yaml(fpath)):
                        errors.append("rooms/official/%s/%s: %s at %s"
                                      % (room, fn, err.message, list(err.absolute_path)))
            emg_path = os.path.join(rdir, "emergence.json")
            if os.path.exists(emg_path) and validators.get("emergence.schema.json"):
                for err in validators["emergence.schema.json"].iter_errors(_load_json(emg_path)):
                    errors.append("rooms/official/%s/emergence.json: %s" % (room, err.message))
            runs_dir = os.path.join(rdir, "runs")
            if os.path.isdir(runs_dir):
                for sd in sorted(os.listdir(runs_dir)):
                    for fn, sfile in [("manifest.json", "run.schema.json"),
                                      ("emergence.json", "emergence.schema.json"),
                                      ("field.json", "field-index.schema.json")]:
                        fpath = os.path.join(runs_dir, sd, fn)
                        if os.path.exists(fpath) and validators.get(sfile):
                            for err in validators[sfile].iter_errors(_load_json(fpath)):
                                errors.append("rooms/official/%s/runs/%s/%s: %s"
                                              % (room, sd, fn, err.message))
            # Phase 0: recorded-field render manifest (viz -> measured physics, machine-readable + honesty)
            rm = os.path.join(rdir, "render-manifest.yaml")
            if os.path.exists(rm) and validators.get("render-manifest.schema.json"):
                for err in validators["render-manifest.schema.json"].iter_errors(_load_yaml(rm)):
                    errors.append("rooms/official/%s/render-manifest.yaml: %s" % (room, err.message))
            n_rooms += 1
        info.append("Genesis Room OK: %d official room(s) validated (room/genesis/emergence/run/dim/render)"
                    % n_rooms)

    # 8. Candidate / rejected rooms (AI Lab, non-official): lighter set -- room.yaml + genesis.yaml +
    #    emergence.json + runs; they must NOT be marked official and must not claim full_3d passed.
    n_cand = 0
    rv = {s: Draft202012Validator(_load_json(os.path.join(_SCHEMAS, s)))
          for s in ("room.schema.json", "genesis.schema.json", "emergence.schema.json", "run.schema.json")
          if os.path.exists(os.path.join(_SCHEMAS, s))}
    for base in ("candidates", "rejected_in_3d"):
        bdir = os.path.join(_REPO, "rooms", base)
        if not os.path.isdir(bdir):
            continue
        for room in sorted(d for d in os.listdir(bdir) if os.path.isdir(os.path.join(bdir, d))):
            rdir = os.path.join(bdir, room)
            ry = os.path.join(rdir, "room.yaml")
            if os.path.exists(ry):
                doc = _load_yaml(ry)
                for err in rv["room.schema.json"].iter_errors(doc):
                    errors.append("rooms/%s/%s/room.yaml: %s" % (base, room, err.message))
                if doc.get("official") is True:
                    errors.append("rooms/%s/%s/room.yaml: a non-official room must not set official=true" % (base, room))
                if doc.get("dimension_status", {}).get("full_3d") == "passed":
                    errors.append("rooms/%s/%s/room.yaml: candidate must not claim full_3d=passed (not promoted)" % (base, room))
            for fn, sfile in [("genesis.yaml", "genesis.schema.json"), ("emergence.json", "emergence.schema.json")]:
                fp = os.path.join(rdir, fn)
                if os.path.exists(fp) and sfile in rv:
                    doc = _load_yaml(fp) if fn.endswith(".yaml") else _load_json(fp)
                    for err in rv[sfile].iter_errors(doc):
                        errors.append("rooms/%s/%s/%s: %s" % (base, room, fn, err.message))
            rundir = os.path.join(rdir, "runs")
            if os.path.isdir(rundir):
                for sd in sorted(os.listdir(rundir)):
                    mp = os.path.join(rundir, sd, "manifest.json")
                    if os.path.exists(mp) and "run.schema.json" in rv:
                        for err in rv["run.schema.json"].iter_errors(_load_json(mp)):
                            errors.append("rooms/%s/%s/runs/%s/manifest.json: %s" % (base, room, sd, err.message))
            n_cand += 1
    if n_cand:
        info.append("Candidate/rejected room OK: %d non-official room(s) validated (official=false, full_3d != passed)"
                    % n_cand)

    for line in info:
        print("  " + line)
    if errors:
        print("\nSCHEMA/REGISTRY VALIDATION FAILED:")
        for e in errors:
            print("  - " + e)
        return 1
    print("\nCI-B OK: %d schemas well-formed; registry validates; refs resolve; ids unique; "
          "%d experiment.yaml + %d Genesis Room(s) validated (schema + 8th-audit)."
          % (len(schema_files), n_exp, n_rooms))
    return 0


if __name__ == "__main__":
    sys.exit(main())
