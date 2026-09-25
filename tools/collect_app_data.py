#!/usr/bin/env python3
"""Assemble app/public/data/ for the Observatory (Phase 1) — the app's read-only data root.

The React app is catalog-driven and NEVER hard-codes room data. This copies the SINGLE source
(catalog.json + each room's recorded field.json + render-manifest) into app/public/data/ so the built
static site can fetch them. No physics, no summaries are recomputed here -- pure copy/normalise.

Dream Loop adds read-only human-facing data under `data/dream/`. These are presentation/event
artifacts only; they do not alter Room physics or scientific status.

Universe Aquarium planning data is copied under `data/aquaria/`. Aquarium intent, human notes and
AI direction notes are collaboration/planning data only: they never alter Room physics, scientific
promotion, or evidence status.

    app/public/data/
      catalog.json
      rooms/<room_id>/field.json           (referenced recorded fields; not inlined in catalog)
      rooms/<room_id>/render-manifest.json  (yaml -> json for the browser)
      dream/latest.json                     (latest Night Report, when present)
      dream/view-presets.json               (observation recipes, when present)
      dream/event-ledger.json               (append-only human-facing event ledger, when present)
      aquaria/registry.json                 (Universe Aquarium research lanes)
      aquaria/notebook.json                 (shared human/AI planning notebook)
"""

import argparse
import json
import os
import shutil
import sys

import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    catalog_path = os.path.join(_REPO, "app", "generated", "catalog.json")
    catalog = json.load(open(catalog_path))
    shutil.copyfile(catalog_path, os.path.join(out_dir, "catalog.json"))

    rooms_out = os.path.join(out_dir, "rooms")
    n = 0
    # official rooms + Live Runner / AI candidate rooms share the same reference structure, so the
    # browser replays both the same way (candidate rooms stay visually/tagged distinct in the UI).
    for room in catalog.get("rooms", []) + catalog.get("candidate_rooms", []):
        rid = room["room_id"]
        src = _room_dir(rid)
        if not src:
            continue
        dst = os.path.join(rooms_out, rid)
        os.makedirs(dst, exist_ok=True)
        # recorded fields (referenced by frames_ref, relative to the room dir)
        fref = room.get("frames_ref")
        if fref and os.path.exists(os.path.join(src, fref)):
            shutil.copyfile(os.path.join(src, fref), os.path.join(dst, "field.json"))
        # render manifest (yaml -> json for the browser)
        rm = os.path.join(src, "render-manifest.yaml")
        if os.path.exists(rm):
            json.dump(yaml.safe_load(open(rm)), open(os.path.join(dst, "render-manifest.json"), "w"),
                      ensure_ascii=False)
        n += 1

    _copy_dream_data(out_dir)
    _copy_aquarium_data(out_dir)
    return n


def _copy_dream_data(out_dir):
    dream_out = os.path.join(out_dir, "dream")
    os.makedirs(dream_out, exist_ok=True)
    sources = {
        "latest.json": os.path.join(_REPO, "ai_lab", "reports", "nightly", "latest.json"),
        "view-presets.json": os.path.join(_REPO, "ai_lab", "discoveries", "view_presets.json"),
        "event-ledger.json": os.path.join(_REPO, "ai_lab", "discoveries", "event_ledger.json"),
    }
    for name, src in sources.items():
        dst = os.path.join(dream_out, name)
        if os.path.exists(src):
            shutil.copyfile(src, dst)
        elif os.path.exists(dst):
            # Avoid serving a stale previous report from an old local build.
            os.remove(dst)


def _copy_aquarium_data(out_dir):
    aquarium_out = os.path.join(out_dir, "aquaria")
    os.makedirs(aquarium_out, exist_ok=True)
    sources = {
        "registry.json": os.path.join(_REPO, "aquaria", "registry.json"),
        "notebook.json": os.path.join(_REPO, "aquaria", "notebook.json"),
    }
    for name, src in sources.items():
        dst = os.path.join(aquarium_out, name)
        if os.path.exists(src):
            shutil.copyfile(src, dst)
        elif os.path.exists(dst):
            os.remove(dst)


def _room_dir(room_id):
    idx = os.path.join(_REPO, "rooms", "catalog.json")
    if os.path.exists(idx):
        for e in json.load(open(idx)).get("rooms", []):
            if e["room_id"] == room_id:
                return os.path.join(_REPO, e["path"])
    # official, then non-official candidate/rejected trees
    for cand in (os.path.join(_REPO, "rooms", "official", room_id),
                 os.path.join(_REPO, "rooms", "candidates", room_id),
                 os.path.join(_REPO, "rooms", "rejected_in_3d", room_id)):
        if os.path.isdir(cand):
            return cand
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Collect Observatory app data into app/public/data/")
    ap.add_argument("--out-dir", default=os.path.join(_REPO, "app", "public", "data"))
    args = ap.parse_args(argv)
    n = build(args.out_dir)
    print("collected %d room(s) into %s" % (n, os.path.relpath(args.out_dir, _REPO)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
