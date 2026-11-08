"""Render recorded 3D fields and every case; pixels never enter the solver."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from material_model_v02 import digest

def main(root,out):
    root=Path(root)/'discovery';out=Path(out)
    selected=root/'coupled-d3-n24-dt0.25-s17'
    state=selected/'state-1600.npz';data=np.load(state);phi=data['phi'];n=phi.shape[0]
    fig,axes=plt.subplots(2,3,figsize=(14,8.4),layout='constrained')
    views=[(phi[n//2,:,:].T,'x = L/2','y','z'),(phi[:,n//2,:].T,'y = L/2','x','z'),(phi[:,:,n//2].T,'z = L/2','x','y')]
    for ax,(view,title,x,y) in zip(axes[0],views):
        im=ax.imshow(view,origin='lower',extent=[0,32,0,32],vmin=-.65,vmax=.65,cmap='RdBu_r',interpolation='nearest')
        ax.set(title=f'3D material field: {title}',xlabel=x,ylabel=y)
    fig.colorbar(im,ax=axes[0],shrink=.8,label='material composition deviation phi')
    groups={};sources={str(state):digest(state)}
    for path in sorted(root.glob('*/series.csv')):
        name=path.parent.name.split('-d')[0];rows=list(csv.DictReader(path.open()));sources[str(path)]=digest(path)
        groups.setdefault(name,[]).append(rows)
    for name,series in groups.items():
        ts=np.array([float(r['time']) for r in series[0]])
        values=np.array([[float(r['std_phi']) for r in rows] for rows in series])
        line=axes[1,0].plot(ts,values.mean(axis=0),label=name)[0]
        axes[1,0].fill_between(ts,values.min(axis=0),values.max(axis=0),color=line.get_color(),alpha=.12)
        chem=np.array([[float(r['mean_complex']) for r in rows] for rows in series])
        axes[1,1].plot(ts,chem.mean(axis=0),label=name)
        F=np.array([[float(r['free_energy'])-float(rows[0]['free_energy']) for r in rows] for rows in series])
        axes[1,2].plot(ts,F.mean(axis=0),label=name)
    axes[1,0].set(title='All seven cases, three seeds',xlabel='time',ylabel='std(phi)')
    axes[1,1].set(title='Bound complex: not replication',xlabel='time',ylabel='mean concentration C',yscale='log')
    axes[1,2].set(title='Free energy dissipated to heat bath',xlabel='time',ylabel='F(t) - F(0)')
    axes[1,0].legend(fontsize=7,loc='upper left')
    fig.suptitle('Bounded reciprocal mixture | preliminary 24^3, L=32, t=400 | no membrane/life claim',fontsize=12)
    fig.savefig(out,dpi=150)
    out.with_suffix('.json').write_text(json.dumps({'physical_inputs_sha256':sources,'display_only':True,
        'central_slices_fixed_before_rendering':True,'color_range':[-.65,.65],
        'shading':'range across three seeds, not a confidence interval','law_scope':'uncalibrated constitutive hypothesis',
        'source_max_abs_phi':float(np.abs(phi).max()),'physics_modified':False},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('out');a=p.parse_args();main(a.root,a.out)
