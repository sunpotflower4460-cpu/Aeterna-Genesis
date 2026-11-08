"""Immutable runs of the prospectively registered thermodynamic mixture."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import sys
import time
import traceback
import numpy as np
from scipy.signal import resample
from material_model import Solver,digest

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from genesis.diagnostics.vessel_geometry_3d import connected_components
from genesis.diagnostics.topology3d import three_d_authenticity

def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def initial(n,d,seed):
    b=9;freq=np.fft.fftfreq(b)*b
    k=np.meshgrid(*([freq]*d),indexing='ij');mask=sum(x*x for x in k)<=9;mask[(0,)*d]=False
    rng=np.random.default_rng(seed)
    phi=np.fft.ifftn(np.fft.fftn(rng.normal(size=(b,)*d))*mask).real;phi*=.01/phi.std()
    for axis in range(d):phi=resample(phi,n,axis=axis)
    phi=np.ascontiguousarray(phi)
    bound=(11-np.sqrt(21))/20
    c=np.empty((3,)+(n,)*d);c[0]=.5-bound;c[1]=.5-bound;c[2]=bound
    return phi,c

def observe(solver,phi,c,t):
    row={'time':t,'free_energy':solver.free_energy(phi,c),'mean_phi':float(phi.mean()),
         'std_phi':float(phi.std()),'min_phi':float(phi.min()),'max_phi':float(phi.max()),
         'atoms_A':float((c[0]+c[2]).mean()),'atoms_B':float((c[1]+c[2]).mean()),
         'mean_complex':float(c[2].mean()),'min_concentration':float(c.min()),
         'phase_substep_rejections':solver.phase_rejections}
    R=.02*solver.rate*(solver.K*c[0]*c[1]-c[2])
    affinity=np.log(solver.K*c[0]*c[1]/c[2])
    row['reaction_dissipation']=float(np.mean(R*affinity))
    row['net_association_rate']=float(R.mean())
    geometries={}
    for threshold in [0.,.1,.2]:
        inside=phi>threshold;outside=phi<(-threshold)
        n,sizes=connected_components(inside)
        key=str(threshold)
        geometries[key]={'count':n,'largest_voxels':sizes[:8],
                          'largest_volume':sizes[0]*solver.dx**solver.d if sizes else 0.,
                          'inside_fraction':float(inside.mean()),'outside_fraction':float(outside.mean())}
        row['inside_fraction_'+key]=float(inside.mean());row['regions_'+key]=n
        if inside.mean()>=.01 and outside.mean()>=.01:
            for i,name in enumerate(['A','B','C']):row[name+'_partition_'+key]=float(c[i][inside].mean()/c[i][outside].mean())
            row['inside_net_reaction_'+key]=float(R[inside].mean())
            row['outside_net_reaction_'+key]=float(R[outside].mean())
        else:
            for name in ['A','B','C']:row[name+'_partition_'+key]=None
            row['inside_net_reaction_'+key]=None;row['outside_net_reaction_'+key]=None
    return row,geometries

def run(out,stage,case,n,seed,dt,d=3,T=400.,L=32.):
    target=Path(out)/stage/f'{case["id"]}-d{d}-n{n}-dt{dt}-s{seed}'
    if target.exists():raise FileExistsError(target)
    target.mkdir(parents=True)
    prereg=HERE/'PRE_REGISTRATION.json'
    recipe={'stage':stage,'case':case,'grid':n,'dimension':d,'L':L,'T':T,'dt':dt,'seed':seed,
            'sources':{p.name:digest(p) for p in [HERE/'material_model.py',HERE/'implicit_transport.cpp',Path(__file__)]},
            'prereg_sha256':digest(prereg),'shape_seeded':False,'starts_at_zero':True,
            'numerical_shortcuts':['implicit periodic line solve','Fourier inversion of local discrete Laplacian'],
            'physical_claim_scope':'dimensionless constitutive hypothesis, not an identified molecule, bilayer or life'}
    save(target/'recipe.json',recipe)
    parameters={k:v for k,v in case.items() if k!='id'}
    solver=Solver((n,)*d,L,**parameters)
    phi,c=initial(n,d,seed);rows=[];frames=[];start=time.monotonic()
    steps=round(T/dt);stride=max(1,round(5/dt))
    initial_atoms=[float((c[i]+c[2]).mean()) for i in range(2)];phi0=float(phi.mean())
    previousF=solver.free_energy(phi,c)
    try:
        for step in range(steps+1):
            if step%stride==0 or step==steps:
                row,geometry=observe(solver,phi,c,step*dt)
                if row['free_energy']>previousF+1e-9:raise FloatingPointError('free-energy increase exceeds roundoff')
                if max(abs(row['atoms_A']-initial_atoms[0]),abs(row['atoms_B']-initial_atoms[1]))>1e-8:raise FloatingPointError('atom balance failed')
                if abs(row['mean_phi']-phi0)>1e-8:raise FloatingPointError('material balance failed')
                rows.append(row);previousF=row['free_energy']
                with (target/'series.csv').open('w',newline='') as f:
                    writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader();writer.writerows(rows)
            if step in [0,steps//4,steps//2,steps]:
                path=target/f'state-{step}.npz';np.savez_compressed(path,phi=phi,concentrations=c)
                record={'file':path.name,'sha256':digest(path),'time':step*dt,'geometry':geometry}
                if d==3:record['three_d_authenticity']=three_d_authenticity(phi)
                frames.append(record)
            if step<steps:phi,c=solver.step(phi,c,dt)
    except Exception as e:
        np.savez_compressed(target/'failed-state.npz',phi=phi,concentrations=c)
        save(target/'FAILURE.json',{'step':step,'time':step*dt,'type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'qualification':False})
        raise
    late=[r for r in rows if 300<=r['time']<=400]
    summary={'wall_seconds':time.monotonic()-start,'numerical_budget_pass':True,'qualified_changes':0,
             'free_energy_initial':rows[0]['free_energy'],'free_energy_final':rows[-1]['free_energy'],
             'atom_drift_max':max(abs(r[key]-.5) for r in rows for key in ['atoms_A','atoms_B']),
             'mean_phi_drift_max':max(abs(r['mean_phi']-phi0) for r in rows),
             'late_phi_std':float(np.mean([r['std_phi'] for r in late])),
             'late_complex_partition':float(np.mean([r['C_partition_0.1'] for r in late if r['C_partition_0.1'] is not None]))
                 if any(r['C_partition_0.1'] is not None for r in late) else None,
             'minimum_phase_substep':solver.minimum_phase_step,'phase_rejections':solver.phase_rejections,
             'frames':frames,'classification':'F, pending controls, material mapping and convergence; not a membrane claim'}
    save(target/'summary.json',summary)
    print(json.dumps({'run':target.name,'seconds':round(summary['wall_seconds'],2),'std_phi':summary['late_phi_std'],
                      'complex_partition':summary['late_complex_partition'],'atom_drift':summary['atom_drift_max'],'phase_rejections':solver.phase_rejections}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['discovery','verify','compare-2d']);p.add_argument('--out',required=True)
    p.add_argument('--grid',type=int);p.add_argument('--seeds');p.add_argument('--cases');p.add_argument('--dt',type=float,default=.25)
    args=p.parse_args();reg=json.loads((HERE/'PRE_REGISTRATION.json').read_text())
    stage=args.stage;n=args.grid or (24 if stage=='discovery' else 32)
    seeds=[int(s) for s in args.seeds.split(',')] if args.seeds else ([17,31,53] if stage=='discovery' else [113,227,349])
    cases=[c for c in reg['cases'] if not args.cases or c['id'] in args.cases.split(',')]
    for seed in seeds:
        for case in cases:run(args.out,stage,case,n,seed,args.dt,2 if stage=='compare-2d' else 3)
