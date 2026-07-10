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

    for line in info:
        print("  " + line)
    if errors:
        print("\nSCHEMA/REGISTRY VALIDATION FAILED:")
        for e in errors:
            print("  - " + e)
        return 1
    print("\nCI-B OK: %d schemas well-formed; registry validates; refs resolve; ids unique."
          % len(schema_files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
