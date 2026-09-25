"""Observation packet: mechanical rules describe known scenes correctly, and the packet is what we save/send."""
import json

import numpy as np
import pytest

from tools.lab import observe
from tools.lab.hub import LocalHub


def _rules(u):
    return [e["rule"] for e in u["events"]]


def test_rules_on_synthetic_series():
    t = np.linspace(0, 100, 400)
    ev = observe.period(t, np.sin(2 * np.pi * t / 20) + 0.01 * t, "x")
    assert ev and abs(ev["period"] - 20) < 1.5
    assert observe.jumps(t, np.full_like(t, 32.0) + 1e-9 * t, "cx") == []          # constant: no jump
    v = np.r_[np.zeros(200), np.ones(200)]
    assert [e["t"] for e in observe.jumps(t, v, "y")] == [pytest.approx(t[200])]
    many = observe.count_changes(t, (t // 5) % 3, "spots")
    assert len(many) == 1 and many[0]["rule"] == "count-change-summary"
    assert observe.settled(t, np.r_[np.linspace(0, 1, 300), np.ones(100)], "a")


def test_periodic_blobs_merge_across_the_edge():
    m = np.zeros((32, 32), bool)
    m[10:14, 0:3] = m[10:14, 30:32] = True          # one blob wrapped around x
    m[20:24, 15:19] = True
    blobs = observe.periodic_blobs(m)
    assert len(blobs) == 2 and sorted(b["area"] for b in blobs) == [16.0, 20.0]


def test_gray_scott_split_and_branch_extinction():
    h = LocalHub()
    a = h.create("gray-scott", 1)
    h.run(a, 30)
    c = h.branch(a, {"F": 0.025, "k": 0.06})
    h.run(c, 12)
    p = observe.build(h, [a, c])
    A, C = p["universes"]
    assert "track:split" in _rules(A)
    assert C["summary"]["spots"]["last"] == 0 and "track:death" in _rules(C)
    assert any(e["rule"] == "置いた（介入）" and "分岐で" in e["text"] for e in C["events"])
    assert "L7-partial" in p["text"] and "宇宙 B" in p["text"]


def test_perturbation_is_bracketed_by_tagged_keyframes():
    h = LocalHub()
    s = h.create("sh", 0)
    h.run(s, 20)
    h.perturb(s, "cut_half")
    h.run(s, 10)
    u = observe.build(h, [s])["universes"][0]
    caps = [im["caption"] for im in u["images"]]
    assert any("before perturb:cut_half" in c for c in caps) and any("after perturb:cut_half" in c for c in caps)
    assert any(im["kind"] == "diff" for im in u["images"])
    assert any(e["rule"] == "置いた（介入）" for e in u["events"])


def test_3d_projections_and_packet_io(tmp_path):
    h = LocalHub()
    b = h.create("tdgl-3d", 0)
    h.run(b, 30)
    g = h.create("gpe-ring-3d", 0)
    h.run(g, 2)
    p = observe.build(h, [b, g])
    B, G = p["universes"]
    assert B["summary"]["defects"]["last"] < B["summary"]["defects"]["max"]
    assert "投影 3 枚" in B["images"][0]["caption"] and B["images"][0]["png"][:4] == b"\x89PNG"
    assert G["ceiling"] is None and "項目なし" in p["text"]
    json.dumps(observe.to_public(p))
    d = observe.save(p, tmp_path / "pk")
    assert (d / "packet.md").read_text(encoding="utf-8") == p["text"]
    assert len(list(d.glob("*.png"))) == len(B["images"]) + len(G["images"])
