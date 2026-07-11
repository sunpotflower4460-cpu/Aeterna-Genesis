#!/usr/bin/env python3
"""Assemble app/public/data/ for the Observatory (Phase 1) — the app's read-only data root.

The React app is catalog-driven and NEVER hard-codes room data. This copies the SINGLE source
(catalog.json + each room's recorded field.json + render-manifest) into app/public/data/ so the built
static site can fetch them. No physics, no summaries are recomputed here -- pure copy/normalise.

    app/public/data/
      catalog.json
      rooms/<room_id>/field.json           (referenced recorded fields; not inlined in catalog)
      rooms/<room_id>/render-manifest.json  (yaml -> json for the browser)
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
    return n


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
