"""P4 aquarium: every template has recorded frames, honest put_in/emerged text, and fits deploy limits."""

import json
import os

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_AQ = os.path.join(_REPO, "app", "public", "aquarium")


def _templates():
    with open(os.path.join(_AQ, "templates.json"), encoding="utf-8") as fh:
        return json.load(fh)["templates"]


def test_templates_are_complete_and_honest():
    tpls = _templates()
    assert len(tpls) >= 8
    assert len({t["id"] for t in tpls}) == len(tpls)
    for t in tpls:
        assert t["put_in"] and t["emerged"], t["id"]           # "placed" is always stated
        assert t["level"] and t["tier"] and t["source"] and t["recipe"], t["id"]
        assert t["default_lens"] in {lens["name"] for lens in t["lenses"]}, t["id"]
        assert all(lens["transfer"] in {"high", "low", "cyclic", "diverging"} for lens in t["lenses"])


def test_recorded_frames_match_templates_and_limits():
    total = 0
    for t in _templates():
        path = os.path.join(_AQ, t["id"], "field.json")
        size = os.path.getsize(path)
        assert size < 24 * 2**20, t["id"]                        # Cloudflare per-file limit is 25 MiB
        total += size
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        assert d["dimension"] == t["dimension"] and len(d["grid"]) == t["dimension"]
        assert d["honesty"]["changes_physics"] is False and d["honesty"]["quantized_uint8"] is True
        assert d["nframes"] == len(d["times"]) >= 8
        for lens in t["lenses"]:
            assert lens["name"] in d["lenses"], (t["id"], lens["name"])
    assert total < 150 * 2**20
