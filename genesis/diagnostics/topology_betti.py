"""Topology Instrument v1 (scalar part): from a 3D binary region (a level set of a scalar field) measure the
Betti numbers b0 (components), b1 (tunnels/handles), b2 (internal cavities), the Euler characteristic chi, and
the boundary-surface genus -- with synthetic positive/negative controls. This is the 3D analog whose SURFACE
facts e046 validates (sphere/torus). Exact cubical-complex chi (no skimage): chi = V - E + F - C over the
union-of-closed-voxels complex. b1 = b0 + b2 - chi. genus (single cavity-free component) = b1.
"""
import numpy as np
from scipy import ndimage


def _count_cells(mask):
    """Vertices, edges, faces, cubes of the cubical complex (union of closed unit voxels of `mask`)."""
    Nx, Ny, Nz = mask.shape
    C = int(mask.sum())
    # vertices (Nx+1,Ny+1,Nz+1): occupied if any of 8 incident voxels filled
    Vg = np.zeros((Nx + 1, Ny + 1, Nz + 1), bool)
    for di in (0, 1):
        for dj in (0, 1):
            for dk in (0, 1):
                Vg[di:di + Nx, dj:dj + Ny, dk:dk + Nz] |= mask
    V = int(Vg.sum())
    # edges along x (Nx,Ny+1,Nz+1); voxel contributes at (i, j+dj, k+dk)
    Ex = np.zeros((Nx, Ny + 1, Nz + 1), bool)
    Ey = np.zeros((Nx + 1, Ny, Nz + 1), bool)
    Ez = np.zeros((Nx + 1, Ny + 1, Nz), bool)
    for dj in (0, 1):
        for dk in (0, 1):
            Ex[:, dj:dj + Ny, dk:dk + Nz] |= mask
    for di in (0, 1):
        for dk in (0, 1):
            Ey[di:di + Nx, :, dk:dk + Nz] |= mask
    for di in (0, 1):
        for dj in (0, 1):
            Ez[di:di + Nx, dj:dj + Ny, :] |= mask
    E = int(Ex.sum() + Ey.sum() + Ez.sum())
    # faces perpendicular to z (Nx,Ny,Nz+1): voxel at (i,j,k) and (i,j,k+1); etc.
    Fz = np.zeros((Nx, Ny, Nz + 1), bool)
    Fx = np.zeros((Nx + 1, Ny, Nz), bool)
    Fy = np.zeros((Nx, Ny + 1, Nz), bool)
    for dk in (0, 1):
        Fz[:, :, dk:dk + Nz] |= mask
    for di in (0, 1):
        Fx[di:di + Nx, :, :] |= mask
    for dj in (0, 1):
        Fy[:, dj:dj + Ny, :] |= mask
    F = int(Fx.sum() + Fy.sum() + Fz.sum())
    return V, E, F, C


def betti3d(mask):
    """Return dict(b0,b1,b2,chi,genus) for a 3D binary region (padded so boundary cells are counted)."""
    m = np.pad(mask.astype(bool), 1)
    _, b0 = ndimage.label(m)                                  # connected components (6-conn)
    V, E, F, C = _count_cells(m)
    chi = V - E + F - C
    # cavities: background components not touching the padded boundary
    bg_lbl, nbg = ndimage.label(~m)
    border = set(np.unique(np.concatenate([
        bg_lbl[0].ravel(), bg_lbl[-1].ravel(), bg_lbl[:, 0].ravel(),
        bg_lbl[:, -1].ravel(), bg_lbl[:, :, 0].ravel(), bg_lbl[:, :, -1].ravel()])))
    b2 = int(sum(1 for lab in range(1, nbg + 1) if lab not in border))
    b1 = b0 + b2 - chi
    genus = b1 if (b0 == 1 and b2 == 0) else None            # boundary genus of a cavity-free handlebody
    return {"b0": int(b0), "b1": int(b1), "b2": int(b2), "chi": int(chi), "genus": genus}


# ---- synthetic controls ----
def _grid(N):
    x = np.arange(N) - (N - 1) / 2.0
    return np.meshgrid(x, x, x, indexing="ij")


def ball(N=40, r=12):
    X, Y, Z = _grid(N)
    return (X**2 + Y**2 + Z**2) < r**2


def two_balls(N=48, r=8, sep=20):
    X, Y, Z = _grid(N)
    return ((X - sep/2)**2 + Y**2 + Z**2 < r**2) | ((X + sep/2)**2 + Y**2 + Z**2 < r**2)


def shell(N=44, ro=16, ri=9):
    X, Y, Z = _grid(N); r2 = X**2 + Y**2 + Z**2
    return (r2 < ro**2) & (r2 > ri**2)


def solid_torus(N=56, R=16, a=6):
    X, Y, Z = _grid(N)
    return (np.sqrt(X**2 + Y**2) - R)**2 + Z**2 < a**2


def double_torus(N=72, R=11, a=5, dx=15):
    X, Y, Z = _grid(N)
    t1 = (np.sqrt((X - dx)**2 + Y**2) - R)**2 + Z**2 < a**2
    t2 = (np.sqrt((X + dx)**2 + Y**2) - R)**2 + Z**2 < a**2
    return t1 | t2


CONTROLS = [
    ("solid_ball", ball, dict(b0=1, b1=0, b2=0, genus=0)),
    ("two_balls", two_balls, dict(b0=2, b1=0, b2=0, genus=None)),
    ("hollow_shell", shell, dict(b0=1, b1=0, b2=1, genus=None)),
    ("solid_torus", solid_torus, dict(b0=1, b1=1, b2=0, genus=1)),
    ("double_torus", double_torus, dict(b0=1, b1=2, b2=0, genus=2)),
]


if __name__ == "__main__":
    allok = True
    for name, fn, exp in CONTROLS:
        got = betti3d(fn())
        ok = all(got[k] == v for k, v in exp.items())
        allok &= ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:14s} got b0={got['b0']} b1={got['b1']} b2={got['b2']} "
              f"chi={got['chi']} genus={got['genus']}  expect {exp}")
    print("STATUS:", "GREEN" if allok else "RED")
