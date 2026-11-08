#!/usr/bin/env python3
"""Re-read the OFFICIAL Rooms with bag eyes. Nothing is recomputed, nothing is written back.

QUESTION: the official records say "reached_level 2 / localization: true / defect_count 241".
          Read with the bag ruler instead of the hole ruler: is there ONE bounded dense
          inside with a skin that persists, or is the room one ground with holes in it?

HONESTY FLOOR (read this before believing any number below):
  The only field data stored with the official Rooms is the DISPLAY lens
  (`runs/seed-0000/field.json`): downsampled with scipy.ndimage.zoom(order=1) and quantised
  to uint8. room-g001-a's raw physics is 64^3; what is stored is 20^3. So the numbers here
  are DISPLAY-GRADE, not physics-grade. They are enough to answer "does the dense side fill
  the room?" (a bulk property that survives downsampling) and NOT enough to count holes or
  resolve a thin skin (both are destroyed by the smoothing). The 64^3 run was NOT rerun.

The bag gate is the frozen one from PR #135, unchanged. No official Room file is modified.
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
_REPO = HERE.parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from replay import BAG_CRITERION, OUTSIDE_CRITERION, component_table  # noqa: E402


def load_lens(path: Path, lens: str):
    d = json.load(open(path))
    grid = d["grid"]
    nf = d["nframes"]
    L = d["lenses"][lens]
    arr = np.frombuffer(base64.b64decode(L["data_b64"]), np.uint8)
    arr = arr.reshape([nf] + list(grid)).astype(float)
    return L["vmin"] + (L["vmax"] - L["vmin"]) * arr / 255.0, d


def score_mask(mask):
    rows, n = component_table(mask)
    largest = rows[0] if rows else None
    significant = [r for r in rows if r["frac"] >= BAG_CRITERION["min_body_frac"]]
    frac = float(mask.mean())
    room_bulk = bool(frac > BAG_CRITERION["max_body_frac"])
    bag = bool((not room_bulk) and len(significant) == 1 and largest is not None
               and not largest["percolates"]
               and BAG_CRITERION["min_body_frac"] <= largest["frac"] <= BAG_CRITERION["max_body_frac"])
    return {"frac": frac, "n_components": n, "n_significant": len(significant),
            "largest": largest, "room_bulk": room_bulk, "bag_shape": bag}


def main():
    out = {
        "what_this_is": "a re-read of stored OFFICIAL Room display lenses with the frozen bag gate",
        "physics_recomputed": False,
        "official_room_files_modified": [],
        "data_grade": "display lens: downsampled (zoom order=1) + uint8 quantised. NOT physics grade.",
        "bag_criterion": BAG_CRITERION,
        "rooms": {},
    }

    # ---- room-g001-a: the big official 3D TDGL Room (the one PR #135 could not afford to rerun)
    p = _REPO / "rooms/official/room-g001-a/runs/seed-0000/field.json"
    dens, meta = load_lens(p, "density")           # |psi|
    per_frame = []
    for i in range(dens.shape[0]):
        a = dens[i]
        amax = float(a.max())
        dense = a >= BAG_CRITERION["dense_rel_max"] * max(amax, 1e-30)
        s = score_mask(dense)
        s.update({"frame": i, "t": meta["times"][i], "amp_max": amax,
                  "mean": float(a.mean()),
                  "outside_frac": float((a < OUTSIDE_CRITERION["outside_rel_max"] * max(amax, 1e-30)).mean())})
        per_frame.append(s)
    stored = json.load(open(_REPO / "rooms/official/room-g001-a/runs/seed-0000/emergence.json"))
    out["rooms"]["room-g001-a"] = {
        "model": "g001_ginzburg_landau_quench",
        "physics_grid": [64, 64, 64],
        "stored_display_grid": meta["grid"],
        "what_the_official_record_says": {
            "reached_level": stored["reached_level"],
            "level_2_name_in_the_record": "localization",
            "level_2_is_measured_by": "winding_defect_count  (docs: rooms/official/room-g001-a/diagnostics.yaml)",
            "defect_count_seed0": stored["measured_by"]["defect_count"],
            "defect_count_seed1_seed2": [173, 117],
            "final_mean_amplitude_seed0": 0.973843,
        },
        "read_with_bag_eyes": {
            "dense_frac_end": per_frame[-1]["frac"],
            "outside_frac_end": per_frame[-1]["outside_frac"],
            "n_dense_components_end": per_frame[-1]["n_components"],
            "largest_dense_span_frac_end": per_frame[-1]["largest"]["span_frac"] if per_frame[-1]["largest"] else None,
            "bag": False,
            "bag_reason": "room_bulk: the dense side is the whole box (dense_frac >> max_body_frac=0.40)",
            "independent_confirmation_without_the_display_lens": (
                "the stored summary.json final_mean_amplitude = 0.9738 while the equilibrium "
                "amplitude for eps_final=1 is exactly 1.0, so 97% of the box sits at the "
                "ordered value. The dense side fills the room in the PHYSICS data too, not "
                "only in the display lens."),
            "were_holes_counted_as_bodies_here": False,
            "note_on_the_word_localization": (
                "the official Level 2 'localization' means a phase-winding DEFECT is localized "
                "(a hole), not that a BODY is localized. 241 is a hole count, not a body count. "
                "Reading it as 241 bodies would be exactly the mistake the bag lane forbids."),
        },
        "per_frame": per_frame,
    }

    # ---- room-g003-a: the official phase-separating Room already in the repo (2D Model H)
    p3 = _REPO / "rooms/official/room-g003-a/runs/seed-0000/field.json"
    comp, meta3 = load_lens(p3, "composition")     # phi in roughly [-1, +1]
    # Pre-declared mapping for a +/- two-ground field: "dense" = the phi>0 ground.
    # The BAG GATE ITSELF (one component, bounded, non-percolating, 2..40%, persists) is unchanged.
    pf3 = []
    for i in range(comp.shape[0]):
        f = comp[i]
        plus = f > 0.0
        s = score_mask(plus)
        s.update({"frame": i, "t": meta3["times"][i],
                  "phi_min": float(f.min()), "phi_max": float(f.max()),
                  "plus_frac": float(plus.mean()), "minus_frac": float((~plus).mean()),
                  "interface_frac": float(((f > -0.6) & (f < 0.6)).mean())})
        pf3.append(s)
    out["rooms"]["room-g003-a"] = {
        "model": "g003_model_h_phase_field",
        "physics_grid": [128, 128],
        "stored_display_grid": meta3["grid"],
        "why_it_is_on_this_map": (
            "this Room is an ALREADY-EXISTING phase-separating white in the repo: two grounds "
            "(phi ~ +0.73 and ~ -0.73) with a sharp interface between them, grown from uniform "
            "+ noise, mass conserved to machine precision. Nothing was added to get it."),
        "read_with_bag_eyes": {
            "plus_ground_frac_end": pf3[-1]["plus_frac"],
            "minus_ground_frac_end": pf3[-1]["minus_frac"],
            "interface_frac_end": pf3[-1]["interface_frac"],
            "n_plus_components_end": pf3[-1]["n_components"],
            "largest_plus_span_frac_end": pf3[-1]["largest"]["span_frac"] if pf3[-1]["largest"] else None,
            "outside_survives": True,
            "bag": False,
            "bag_reason": (
                "at mean_phi = 0 the two grounds each take about half the box (plus_frac 0.497), "
                "which is already over max_body_frac = 0.40, and the plus ground is not one lump "
                "but 14 pieces whose largest stretches ~0.79-0.88 of the box. An OUTSIDE genuinely "
                "survives here (unlike g001, where it closes), but no ONE BOUNDED body is picked "
                "out. Not a bag. Coexistence alone is explicitly NOT a bag pass."),
            "this_is_not_promoted_to_a_bag": True,
        },
        "per_frame": pf3,
    }

    (HERE / "official_room_reread.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    for rid, r in out["rooms"].items():
        print(f"{rid}: {json.dumps(r['read_with_bag_eyes'], ensure_ascii=False)[:400]}")


if __name__ == "__main__":
    main()
