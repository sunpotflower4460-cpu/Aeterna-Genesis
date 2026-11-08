"""Read-only all-outcome summaries and registered energy-grid visualizations."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import experiment as model

HERE=Path(__file__).resolve().parent


def main(raw,out):
    raw,out=Path(raw),Path(out);out.mkdir(parents=True,exist_ok=False)
    reg=json.loads((HERE/'ENERGY_GRID_REGISTRATION.json').read_text())
    slots=[];hashes={}
    for seed in reg['seeds']:
        selection=raw/'energy-grid'/f'selection-s{seed}.json'
        hashes[str(selection)]=model.digest(selection)
        plan=json.loads(selection.read_text())
        assert len(plan['slots'])==40
        for item in plan['slots']:
            case=item['case']
            path=Path(item['path']) if item['reuses_existing_history'] else raw/'energy-grid'/f'{case["id"]}-d3-n24-T300-s{seed}'
            for name in ['recipe.json','summary.json','series.csv']:
                hashes[str(path/name)]=model.digest(path/name)
            s=json.loads((path/'summary.json').read_text());r=json.loads((path/'recipe.json').read_text())
            assert s['numerical_budget_pass'] and r['seed']==seed and r['parameters']==model.parameters(case)
            f=s['frames'][-1]
            slots.append({'mu':case['mu'],'df':case['df'],'ts_fraction':case['ts_fraction'],'seed':seed,
                'path':str(path),'reused':item['reuses_existing_history'],'late_B_fraction':s['late_B_fraction'],
                'late_work_rate_per_particle':s['late_work_per_particle_time'],
                'final_density_variance':f['density_variances']['4']['material'],
                'final_dense_fraction':f['regions']['0.5']['fraction'],
                'final_dense_volumes':f['regions']['0.5']['largest_volumes'],
                'final_3d_authenticity':f['three_d_authenticity']})
    assert len(slots)==120 and sum(s['reused'] for s in slots)==12
    model.save(out/'grid.json',{'role':'F: finite-time conditional model map, not a phase diagram or three discoveries',
        'qualified_changes':0,'slots':slots,'input_hashes':hashes,'unique_new_grid_histories':108,
        'reused_histories_not_independent':12,'physics_modified':False})
    fig,axes=plt.subplots(2,3,figsize=(15,9),layout='constrained')
    quantities=[('final_density_variance','Final density variance (width 4)',0,.12),
                ('late_B_fraction','Late fraction of B molecules',0,1),
                ('final_dense_fraction','Fraction of box above density .5',0,.2)]
    for row,ts in enumerate(reg['ts_fraction']):
        for col,(key,title,lo,hi) in enumerate(quantities):
            a=np.zeros((len(reg['mu']),len(reg['df'])))
            spread=np.zeros_like(a)
            for i,mu in enumerate(reg['mu']):
                for j,df in enumerate(reg['df']):
                    values=[s[key] for s in slots if s['mu']==mu and s['df']==df and s['ts_fraction']==ts]
                    assert len(values)==3;a[i,j]=np.mean(values);spread[i,j]=np.ptp(values)
            ax=axes[row,col];im=ax.imshow(a,origin='lower',vmin=lo,vmax=hi,cmap='viridis',aspect='auto')
            ax.set(title=f'{title}\nsaddle contact fraction = {ts:g}',xlabel='intrinsic B energy df',ylabel='chemical drive mu',
                   xticks=range(len(reg['df'])),xticklabels=reg['df'],yticks=range(len(reg['mu'])),yticklabels=reg['mu'])
            for i in range(a.shape[0]):
                for j in range(a.shape[1]):ax.text(j,i,f'{a[i,j]:.3f}\nrange {spread[i,j]:.3f}',ha='center',va='center',fontsize=8,color='white' if a[i,j]<(lo+hi)/2 else 'black')
            fig.colorbar(im,ax=ax,shrink=.75)
    fig.suptitle('Complete shape-free 3D energy grid | 24^3, t=300, three seeds per point\n'
                 'Numbers: mean and full seed range; finite-time structures, not membranes or a phase boundary',fontsize=12)
    fig.savefig(out/'energy-map.png',dpi=160)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('out');a=p.parse_args();main(a.raw,a.out)
