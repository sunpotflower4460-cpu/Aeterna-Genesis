"""Preregistered, shape-free classical field exploration; existing core is read-only.

The fast stencil is validated against genesis.models.sb_universe before runs.
Outputs refuse overwrite; every run, including controls and failures, is retained.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from scipy.signal import resample

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from genesis.models import sb_universe as sb
from genesis.diagnostics.topology3d import three_d_authenticity
from genesis.diagnostics.vessel_geometry_3d import connected_components

PREREG = json.loads((HERE / 'PRE_REGISTRATION.json').read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def binary():
    source = HERE/'local_solver.cpp'
    out = Path('/tmp')/('aeterna-mixtures-'+sha(source)[:16])
    if not out.exists():
        subprocess.run(['g++', '-O3', '-std=c++17', '-fopenmp', str(source), '-o', str(out)], check=True)
    return out

def spec(g=0., speed=1., convex=False):
    terms=[]
    for i in range(2):
        if convex:
            terms += [{'kind':'mass','on':f'complex:{i}','m2':.025},
                      {'kind':'aniso','on':f'complex:{i}','kappa':.01}]
        else:
            terms += [{'kind':'triple_well','on':f'complex:{i}','lam':.02,'v':1.},
                      {'kind':'mass','on':f'complex:{i}','m2':.005}]
    terms += [{'kind':'cross','a':'complex:0','b':'complex:1','g':g}]
    return sb.spec_from(complex=2, c_complex=speed, terms=terms)

def unpack(u, d):
    shape=u.shape[1:]
    return {'r':np.zeros((0,)+shape),'pr':np.zeros((0,)+shape),
            'c':np.stack([u[0]+1j*u[1],u[2]+1j*u[3]]),
            'pc':np.stack([u[4]+1j*u[5],u[6]+1j*u[7]]),
            'th':np.zeros((d,)+shape),'E':np.zeros((d,)+shape),'tau':0.}

def pack(st):
    z,p=st['c'],st['pc']
    return np.stack([z[0].real,z[0].imag,z[1].real,z[1].imag,p[0].real,p[0].imag,p[1].real,p[1].imag])

def execute(u, out, length, dt, duration, g, convex=False):
    out=Path(out)
    out.mkdir(parents=True, exist_ok=False)
    u.astype('<f8').tofile(out/'input.bin')
    n,d=u.shape[1],u.ndim-1
    nsteps=round(duration/dt)
    start=time.monotonic()
    subprocess.run([str(binary()),str(n),str(d),str(n/length),str(dt),str(nsteps),
                    str(max(1,round(10/dt))),'.02','.005',str(g),str(int(convex)),
                    str(out/'input.bin'),str(out)],check=True,
                    env={**os.environ,'OMP_NUM_THREADS':'3'})
    return time.monotonic()-start

def validate(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    checks=[]
    rng=np.random.default_rng(991)
    for d in [3,2]:  # actual 3D validation first
        for g,convex in [(-.01,False),(.01,False),(0.,True)]:
            n=8;u=rng.normal(0,.15,(8,)+(n,)*d)
            work=out/f'd{d}-g{g}-convex{convex}'
            execute(u,work,12.,.025,1.,g,convex)
            actual=np.fromfile(work/'state-40.bin').reshape(u.shape)
            s=spec(g,n/12.,convex);st=unpack(u,d)
            for _ in range(40): st=sb.step(s,st,.025)
            err=float(np.max(np.abs(actual-pack(st))))
            assert err<2e-12,err
            rows=list(csv.DictReader((work/'series.csv').open()))
            E=sb.energy(s,unpack(u,d));Ecpp=float(rows[0]['energy'])
            assert abs(E-Ecpp)<1e-12,(E,Ecpp)
            checks.append({'dim':d,'g':g,'convex':convex,'steps':40,'max_reference_error':err,
                           'energy_reference_error':abs(E-Ecpp)})
    save(out/'validation.json',{'checks':checks,'source_sha256':sha(HERE/'local_solver.cpp'),
         'reference_sha256':sha(ROOT/'genesis/models/sb_universe.py')})
    print(json.dumps({'validated':len(checks),'max_error':max(x['max_reference_error'] for x in checks)}),flush=True)

def noise(n,d,seed):
    rng=np.random.default_rng(seed); b=9
    modes=np.fft.fftfreq(b)*b
    k=np.meshgrid(*([modes]*d),indexing='ij')
    mask=sum(x*x for x in k)<=9
    mask[(0,)*d]=False
    a=np.fft.ifftn(np.fft.fftn(rng.normal(size=(b,)*d))*mask).real
    a/=a.std()
    for axis in range(d): a=resample(a,n,axis=axis)
    return a

def initial(n,d,seed,control=None):
    a=.5;omega=np.sqrt(.005+.02*(a*a-1)*(3*a*a-1))
    u=np.zeros((8,)+(n,)*d)
    for q in range(4): u[q]=.02*a*noise(n,d,seed*7+q)
    u[0]+=a;u[2]+=a
    u[5]=omega*a;u[7]=-omega*a  # same reference rotation for every coupling
    if control=='neutral':u[4:]=0.
    if control=='single':u[[2,3,6,7]]=0.
    return u

def analyse(out,n,d,length,wall_seconds):
    out=Path(out);shape=(8,)+(n,)*d
    rows=[{k:float(v) for k,v in r.items()} for r in csv.DictReader((out/'series.csv').open())]
    e0=rows[0]['energy'];q0=[rows[0]['q1'],rows[0]['q2']]
    source_finite=all(r['finite']==1 and all(np.isfinite(v) for v in r.values()) for r in rows)
    drift=max(abs(r['energy']-e0)/abs(e0) for r in rows)
    qdrift=[max(abs(r[f'q{i+1}']-q0[i]) for r in rows) for i in range(2)]
    series_corr=[]
    for r in rows:
        denom=np.sqrt(max(0.,r['var_s1']*r['var_s2']))
        series_corr.append(r['cov_s1_s2']/denom if denom>1e-20 else None)
    late=[i for i,r in enumerate(rows) if 350<=r['time']<=500]
    frames=[]
    for path in sorted(out.glob('state-*.bin'),key=lambda p:int(p.stem.split('-')[1])):
        u=np.fromfile(path).reshape(shape)
        if not np.isfinite(u).all():
            frames.append({'file':path.name,'sha256':sha(path),'finite':False,'geometry_not_evaluated':True})
            continue
        densities=[u[0]**2+u[1]**2,u[2]**2+u[3]**2]
        data={'file':path.name,'sha256':sha(path),'step':int(path.stem.split('-')[1]),'regions':[]}
        if d==3:data['three_d_authenticity']=three_d_authenticity(densities[0])
        for density in densities:
            regions={}
            for threshold in [1.5,2.,3.]:
                mask=density>threshold*density.mean()
                count,sizes=connected_components(mask)
                regions[str(threshold)]={'count':count,'largest_voxels':sizes[:8],
                    'largest_volume':(sizes[0]*(length/n)**d if sizes else 0.),
                    'occupied_fraction':float(mask.mean())}
            data['regions'].append(regions)
        frames.append(data)
    summary={'wall_seconds':wall_seconds,'energy_drift_max_relative':drift,'charge_abs_drift':qdrift,
             'charge_initial':q0,'finite':all(r['finite']==1 for r in rows),
             'late_mean_correlation':float(np.mean([series_corr[i] for i in late if series_corr[i] is not None]))
                 if any(series_corr[i] is not None for i in late) else None,
             'late_cv_density':[float(np.mean([np.sqrt(max(0.,rows[i][f'var_s{k}']))/max(rows[i][f'mean_s{k}'],1e-30)
                                                for i in late])) for k in [1,2]],
             'numerical_budget_pass':source_finite and drift<=.01 and all(x<=1e-8*max(abs(q),1.) for x,q in zip(qdrift,q0)),
             'frames':frames,'qualified_changes':0,'classification':'exploration, pending controls and holdout verification'}
    save(out/'summary.json',summary)
    return summary

def campaign(out,stage,n=None,seeds=None,dt=.15,case_filter=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    validation=json.loads((out/'validation'/'validation.json').read_text())
    assert validation['source_sha256']==sha(HERE/'local_solver.cpp'),'revalidate modified accelerator'
    d=2 if stage=='compare-2d' else 3
    n=n or (48 if stage=='discovery' else 64)
    seeds=seeds or ([11,23,37] if stage=='discovery' else [101,211,307])
    cases=[('attractive',-.01,None),('uncoupled',0.,None),('repulsive',.01,None),
           ('single',0.,'single'),('neutral',0.,'neutral'),('convex',0.,'convex')]
    if case_filter:cases=[c for c in cases if c[0] in case_filter]
    for seed in seeds:
        for name,g,control in cases:
            target=out/stage/f'{name}-d{d}-n{n}-dt{dt}-s{seed}'
            if target.exists():
                if not (target/'summary.json').exists():raise RuntimeError(f'incomplete existing run: {target}')
                continue
            u=initial(n,d,seed,control)
            recipe={'dimension':d,'grid':n,'length':64.,'dt':dt,'duration':500.,'seed':seed,'g':g,'control':control,
                    'put_in':['field content and potential','uniform amplitude and opposite uniform conserved charges',
                              'weak isotropic low-mode fluctuations','periodic box'],'shape_seeded':False,
                    'prereg_sha256':sha(HERE/'PRE_REGISTRATION.json'),'source_sha256':sha(HERE/'local_solver.cpp'),
                    'omega_reference':'uncoupled homogeneous equation, identical across g'}
            elapsed=execute(u,target,64.,dt,500.,g,control=='convex');save(target/'recipe.json',recipe)
            summary=analyse(target,n,d,64.,elapsed)
            print(json.dumps({'run':str(target),'seconds':round(elapsed,2),'energy_drift':summary['energy_drift_max_relative'],
                              'correlation':summary['late_mean_correlation'],'density_cv':summary['late_cv_density'],
                              'budgets_pass':summary['numerical_budget_pass']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['validate','discovery','verify','compare-2d']);p.add_argument('--out',required=True)
    p.add_argument('--grid',type=int);p.add_argument('--seeds');p.add_argument('--dt',type=float,default=.15);p.add_argument('--cases')
    a=p.parse_args()
    if a.stage=='validate':validate(Path(a.out)/'validation')
    else:campaign(a.out,a.stage,a.grid,[int(x) for x in a.seeds.split(',')] if a.seeds else None,a.dt,a.cases.split(',') if a.cases else None)
