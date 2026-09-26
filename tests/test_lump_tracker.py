"""Lump tracker: periodic n-D detection, walls kept apart from lumps, links that respect the speed limit."""
import numpy as np

from genesis.diagnostics.lump_tracker import Tracker, detect


def blob(shape, center, width=2.0, amp=1.0):
    grids = np.meshgrid(*[np.arange(n) for n in shape], indexing="ij")
    d2 = sum(np.minimum(abs(g - c), n - abs(g - c)) ** 2 for g, c, n in zip(grids, center, shape))
    return amp * np.exp(-d2 / (2 * width ** 2))


def test_moving_lump_across_the_edge_and_a_death():
    shape, tr = (64, 64), Tracker((64, 64), c=1.0, margin=2.0)
    for k in range(20):
        t = 5.0 * k
        f = blob(shape, (32, (50 + 0.5 * t) % 64))            # speed 0.5, crosses x = 64 -> 0
        if k < 10:
            f = f + blob(shape, (10, 10))                     # a second lump that disappears at k = 10
        lumps, ext = detect(f, 0.2, max_extent=16)
        assert not ext
        tr.add(t, lumps)
    s = tr.summary()
    moving = max(s["tracks"], key=lambda x: x["lifetime"])
    assert moving["lifetime"] == 95.0 and moving["end"] == "alive"
    assert abs(moving["mean_speed"] - 0.5) < 0.05 and abs(moving["net_displacement"] - 47.5) < 1.0
    assert s["events"]["death"] == 1 and s["events"]["birth"] == 0


def test_nothing_is_linked_faster_than_light():
    shape, tr = (64, 64), Tracker((64, 64), c=1.0, margin=2.0)
    tr.add(0.0, detect(blob(shape, (32, 10)), 0.2, 16)[0])
    tr.add(1.0, detect(blob(shape, (32, 30)), 0.2, 16)[0])     # 20 cells in 1 time unit: not the same lump
    s = tr.summary()
    assert len(s["tracks"]) == 2 and s["events"] == {"birth": 1, "death": 1, "split": 0, "merge": 0}


def test_walls_are_not_lumps_and_3d_works():
    f = np.zeros((32, 32))
    f[10:13, :] = 1.0                                          # a wall spanning the periodic box
    f += blob((32, 32), (25, 5))
    lumps, ext = detect(f, 0.2, max_extent=12)
    assert len(lumps) == 1 and len(ext) == 1 and ext[0]["extent"][1] == 32
    shape = (24, 24, 24)
    tr = Tracker(shape)
    for k in range(5):
        tr.add(float(k), detect(blob(shape, (12, 12, (22 + 0.6 * k) % 24)), 0.2, 8)[0])   # wraps in z
    s = tr.summary()
    assert len(s["tracks"]) == 1 and abs(s["tracks"][0]["mean_speed"] - 0.6) < 0.05
