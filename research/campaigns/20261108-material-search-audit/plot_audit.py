"""Plot the portable evidence archive. Rendering never calls the physical solver."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main(evidence, out):
    evidence, out = Path(evidence), Path(out)
    hashes = {}
    def read(path):
        hashes[str(path.relative_to(evidence))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return list(csv.DictReader(path.open()))
    source = evidence / 'material-states.npz'
    hashes[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
    with np.load(source) as states:
        phi = states['holdout48_coupled__t400__phi']
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.5), layout='constrained')
    n = phi.shape[0]
    views = [(phi[n//2,:,:].T, 'x', 'y', 'z'),
             (phi[:,n//2,:].T, 'y', 'x', 'z'),
             (phi[:,:,n//2].T, 'z', 'x', 'y')]
    for ax, (field, fixed, x, y) in zip(axes[0], views):
        im = ax.imshow(field, extent=(0,32,0,32), origin='lower', vmin=-.65, vmax=.65,
                       cmap='RdBu_r', interpolation='nearest')
        ax.set(title=f'3D central slice: {fixed} = 16', xlabel=x, ylabel=y)
    fig.colorbar(im, ax=axes[0], shrink=.8, label='composition deviation phi (dimensionless)')
    discovery = evidence / 'histories/reactive-mixture-v02/discovery'
    names = ['coupled', 'frozen_reaction', 'slow_binding', 'weak_binding',
             'no_affinity', 'stiff_material', 'high_repulsion']
    for name in names:
        series = [read(p) for p in sorted(discovery.glob(f'{name}-*/series.csv'))]
        assert len(series) == 3
        t = [float(r['time']) for r in series[0]]
        values = np.array([[float(r['std_phi']) for r in rows] for rows in series])
        style = '--' if name == 'frozen_reaction' else ':' if name == 'slow_binding' else '-'
        line = axes[1,0].plot(t, values.mean(axis=0), style, label=name)[0]
        axes[1,0].fill_between(t, values.min(axis=0), values.max(axis=0),
                              color=line.get_color(), alpha=.12)
    axes[1,0].set(title='All cases, three discovery seeds', xlabel='time', ylabel='std(phi)')
    axes[1,0].legend(fontsize=7)
    verification = evidence / 'histories/reactive-mixture-v02/verify'
    recovery = evidence / 'histories/reactive-mixture-v02-recovery/verify'
    for case in ['coupled', 'frozen_reaction', 'weak_binding']:
        xs=[];ys=[]
        for grid in [32,48]:
            p = verification / f'{case}-d3-n{grid}-dt0.25-s113/summary.json'
            if not p.exists():p = recovery / p.parent.name / p.name
            hashes[str(p.relative_to(evidence))] = hashlib.sha256(p.read_bytes()).hexdigest()
            xs.append(grid);ys.append(json.loads(p.read_text())['late_phi_std'])
        axes[1,1].plot(xs,ys,'o-',label=case)
    axes[1,1].set(title='Same holdout seed 113; same box', xlabel='grid per axis',
                  ylabel='late std(phi)', yscale='log', xticks=[32,48])
    axes[1,1].legend(fontsize=8)
    for case in ['coupled','frozen_reaction','weak_binding']:
        p = verification / f'{case}-d3-n32-dt0.25-s113/series.csv'
        rows = read(p)
        t=[float(r['time']) for r in rows]
        for name in ['free_energy']:
            initial=float(rows[0][name])
            axes[1,2].plot(t,[float(r[name])-initial for r in rows],label=case)
    axes[1,2].set(title='Free-energy density dissipates', xlabel='time', ylabel='f(t) - f(0), f = F / volume')
    axes[1,2].legend(fontsize=8)
    fig.suptitle('Shape-free 3D material mixture | t=400, L=32, 48^3 holdout slices\n'
                 'Reaction-frozen control retains concentration: no membrane, metabolism or life claim', fontsize=12)
    fig.savefig(out,dpi=160)
    out.with_suffix('.json').write_text(json.dumps({'display_only':True,'physics_modified':False,
        'source_sha256':hashes,'slice_selection':'fixed central planes, first registered holdout seed, finest tested grid',
        'color_limits':[-.65,.65],'shading':'full range of three seeds, not a confidence interval',
        'all_discovery_cases_shown':names,'source_max_abs_phi':float(np.abs(phi).max())},indent=2)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('evidence');p.add_argument('out');a=p.parse_args()
    main(a.evidence,a.out)
