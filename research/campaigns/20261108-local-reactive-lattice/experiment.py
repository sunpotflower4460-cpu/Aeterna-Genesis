"""Immutable histories of the preregistered local molecular exclusion model."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

import numpy as np
from scipy.ndimage import uniform_filter

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from genesis.diagnostics.topology3d import three_d_authenticity,three_axis_percolation
from genesis.diagnostics.vessel_geometry_3d import connected_components


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def binary():
    source=HERE/'local_kmc.cpp';out=Path('/tmp')/('aeterna-local-kmc-'+digest(source)[:16])
    if not out.exists():subprocess.run(['g++','-O3','-std=c++17',str(source),'-o',str(out)],check=True)
    return out


def parameters(case):
    reg=json.loads((HERE/'PRE_REGISTRATION.json').read_text())
    return reg['defaults']|{k:v for k,v in case.items() if k!='id'}


def fields(path,n,d,sample):
    prefix=Path(path)/f'state-{sample}'
    cells=np.fromfile(str(prefix)+'-cells.bin',dtype=np.uint8).reshape((n,)*d,order='F')
    pos=np.fromfile(str(prefix)+'-positions.bin',dtype='<i4')
    conformers=np.fromfile(str(prefix)+'-conformers.bin',dtype=np.uint8)
    displacements=np.fromfile(str(prefix)+'-displacements.bin',dtype='<i8').reshape(-1,d)
    assert len(pos)==len(conformers)==len(displacements)
    assert np.unique(pos).size==len(pos)
    assert np.array_equal(cells.ravel(order='F')[pos],conformers+1)
    return cells,pos,conformers,displacements


def analyse(path,recipe,elapsed):
    path=Path(path);n,d,T=recipe['N'],recipe['dimension'],recipe['T']
    rows=list(csv.DictReader((path/'series.csv').open()))
    assert float(rows[0]['time'])==0 and float(rows[-1]['time'])==T
    for row in rows:
        assert all(np.isfinite(float(v)) for v in row.values())
        assert int(row['molecules'])==recipe['molecules']
        scale=max(1.,abs(float(row['work'])),abs(float(row['H'])-float(rows[0]['H'])))
        assert abs(float(row['heat_budget_error']))/scale<=1e-10
    observations=[]
    for sample in sorted({0,round(T/10)//4,round(T/10)//2,round(T/10)}):
        cells,pos,_,_=fields(path,n,d,sample)
        assert np.count_nonzero(cells)==recipe['molecules']
        record={'sample':sample,'time':sample*10,'files':{p.name:digest(p) for p in sorted(path.glob(f'state-{sample}-*.bin'))},
                'B_fraction_of_molecules':float(np.count_nonzero(cells==2)/recipe['molecules']),
                'density_variances':{},'regions':{}}
        for width in [2,4]:
            rho=uniform_filter((cells>0).astype(float),size=width,mode='wrap')
            b=uniform_filter((cells==2).astype(float),size=width,mode='wrap')
            record['density_variances'][str(width)]={'material':float(rho.var()),'B':float(b.var())}
        for threshold in [.3,.5,.7]:
            mask=rho>threshold;count,sizes=connected_components(mask)
            record['regions'][str(threshold)]={'count':count,'largest_volumes':sizes[:8],'fraction':float(mask.mean())}
            if d==3:record['regions'][str(threshold)]['nonperiodic_span_diagnostic']=three_axis_percolation(mask)
        if d==3:record['three_d_authenticity']=three_d_authenticity(rho)
        observations.append(record)
    half=round(T/10)//2;last=round(T/10)
    old,positions,_,_=fields(path,n,d,half);final,newpositions,_,_=fields(path,n,d,last)
    oldrho=uniform_filter((old>0).astype(float),size=4,mode='wrap').ravel(order='F')
    newrho=uniform_filter((final>0).astype(float),size=4,mode='wrap').ravel(order='F')
    retention={}
    for threshold in [.3,.5,.7]:
        tagged=oldrho[positions]>threshold
        now=newrho[newpositions]>threshold
        retention[str(threshold)]={'molecules_in_old_dense_group':int(tagged.sum()),
            'fraction_still_in_a_dense_region':float(now[tagged].mean()) if tagged.any() else None,
            'fraction_all_molecules_in_final_dense_region':float(now.mean()),
            'labels_are_read_only':True,'warning':'conditional residence at two times; not continuous residence or a membrane-permeability measurement'}
    late=[r for r in rows if .7*T<=float(r['time'])<=T]
    a,b=late[0],late[-1];duration=float(b['time'])-float(a['time'])
    flux={}
    for key in rows[0]:
        if key.startswith(('rxn_','hop_')):flux[key]=(int(b[key])-int(a[key]))/(duration*n**d) if duration else None
    summary={'role':'F, conditional microscopic lattice observations, not a calibrated material or membrane',
             'qualified_changes':0,'wall_seconds':elapsed,'numerical_budget_pass':True,
             'max_absolute_heat_budget_error':max(abs(float(r['heat_budget_error'])) for r in rows),
             'late_B_fraction':float(np.mean([int(r['B'])/recipe['molecules'] for r in late])),
             'late_work_per_particle_time':(float(b['work'])-float(a['work']))/(duration*recipe['molecules']) if duration else None,
             'frames':observations,'identity_retention':retention,'late_flux_per_volume_time':flux}
    save(path/'summary.json',summary)
    return summary


def run(out,stage,case,n=24,d=3,T=300.,seed=19,density=.18,molecules=None):
    path=Path(out)/stage/f'{case["id"]}-d{d}-n{n}-T{T:g}-s{seed}'
    path.mkdir(parents=True,exist_ok=False)
    p=parameters(case);molecules=round(density*n**d) if molecules is None else molecules
    recipe={'case':case,'parameters':p,'N':n,'dimension':d,'T':T,'seed':seed,'molecules':molecules,
        'density':molecules/n**d,'starts_at_zero':True,'shape_seeded':False,'molecular_spacing':1.,
        'numerical_dt':None,'method':'exact constant-bound null-event CTMC; sampling interval 10',
        'sources':{str(x.relative_to(ROOT)):digest(x) for x in [HERE/'local_kmc.cpp',Path(__file__),HERE/'PRE_REGISTRATION.json']},
        'versions':{'python':platform.python_version(),'numpy':np.__version__},
        'qualified_changes':0,'material_mapping':'hypothetical contact and saddle energies, no named-molecule calibration'}
    save(path/'recipe.json',recipe);start=time.monotonic()
    args=[str(binary()),str(n),str(d),str(molecules),str(T),str(seed)]+[
        str(p[k]) for k in ['epsilon','df','mu','eta','ts_fraction','D','rate']]+[str(path)]
    try:
        with (path/'solver.log').open('w') as log:subprocess.run(args,check=True,stdout=log,stderr=log)
        summary=analyse(path,recipe,time.monotonic()-start)
    except Exception as e:
        save(path/'FAILURE.json',{'type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),
             'qualified_changes':0,'retained_without_repair':True})
        raise
    print(json.dumps({'run':path.name,'seconds':round(summary['wall_seconds'],2),
        'B_fraction':summary['late_B_fraction'],'work_rate':summary['late_work_per_particle_time'],
        'coarse_density_variance':summary['frames'][-1]['density_variances']['4']['material'],
        'largest_region':summary['frames'][-1]['regions']['0.5']['largest_volumes'][:1]}),flush=True)
    return path


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['discovery','verify','compare-2d'])
    parser.add_argument('--out',required=True);parser.add_argument('--N',type=int);parser.add_argument('--T',type=float)
    parser.add_argument('--seeds');parser.add_argument('--cases');args=parser.parse_args()
    reg=json.loads((HERE/'PRE_REGISTRATION.json').read_text())
    seeds=[int(x) for x in args.seeds.split(',')] if args.seeds else (reg['discovery']['seeds'] if args.stage=='discovery' else reg['verification']['holdout_seeds'])
    cases=[c for c in reg['cases'] if not args.cases or c['id'] in args.cases.split(',')]
    for seed in seeds:
        for case in cases:run(args.out,args.stage,case,n=args.N or (24 if args.stage=='discovery' else 32),
            d=2 if args.stage=='compare-2d' else 3,T=args.T or (300. if args.stage=='discovery' else 1000.),seed=seed)
