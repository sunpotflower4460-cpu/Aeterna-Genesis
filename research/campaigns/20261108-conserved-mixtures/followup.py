"""Prospective finite-size, time-horizon and exact-symmetry controls.

Read FOLLOWUP_REGISTRATION.json before running. Each history starts at t=0.
No existing run or source model is edited; all additional runs are preserved.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.signal import resample
import run as base

def large_initial(n,seed):
    # Same physical k cutoff and RMS as the L=64 realization, in a genuinely
    # larger independent volume (NOT copies tiled from a small periodic box).
    d=3;b=17
    modes=np.fft.fftfreq(b)*b
    k=np.meshgrid(modes,modes,modes,indexing='ij')
    mask=sum(x*x for x in k)<=36;mask[0,0,0]=False
    u=np.zeros((8,n,n,n))
    for q in range(4):
        rng=np.random.default_rng(seed*7+q)
        a=np.fft.ifftn(np.fft.fftn(rng.normal(size=(b,b,b)))*mask).real
        a/=a.std()
        for axis in range(d):a=resample(a,n,axis=axis)
        u[q]=.01*a
    u[0]+=.5;u[2]+=.5
    omega=np.sqrt(.00875);u[5]=.5*omega;u[7]=-.5*omega
    return u

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['duration','size','symmetry','dt']);p.add_argument('--root',required=True)
    a=p.parse_args();root=Path(a.root)
    for name,g in [('attractive',-.01),('uncoupled',0.),('repulsive',.01)]:
        n=96 if a.kind in ['size','dt'] else 48;L=128. if a.kind=='size' else 64.
        dt=.075 if a.kind=='dt' else .15;T=1000. if a.kind=='duration' else 500.
        seed=101 if a.kind=='dt' else 11
        out=root/a.kind/f'{name}-n{n}-L{L}-dt{dt}-T{T}-s{seed}'
        u=large_initial(n,seed) if a.kind=='size' else base.initial(n,3,seed)
        if a.kind=='symmetry':
            u[2]=u[0];u[3]=-u[1];u[6]=u[4];u[7]=-u[5]
        seconds=base.execute(u,out,L,dt,T,g)
        recipe={'dimension':3,'grid':n,'length':L,'dt':dt,'duration':T,'seed':seed,'g':g,'control':a.kind,
                'initial_mode_cutoff_physical':3*2*np.pi/64,'shape_seeded':False,'charge_placed':True,
                'source_sha256':base.sha(base.HERE/'local_solver.cpp'),
                'prereg_sha256':base.sha(base.HERE/'PRE_REGISTRATION.json'),
                'followup_registration_sha256':base.sha(base.HERE/'FOLLOWUP_REGISTRATION.json'),
                'runner_sha256':base.sha(__file__)}
        base.save(out/'recipe.json',recipe)
        summary=base.analyse(out,n,3,L,seconds)
        print(json.dumps({'kind':a.kind,'case':name,'seconds':round(seconds,2),
                          'energy_drift':summary['energy_drift_max_relative'],'budget_pass':summary['numerical_budget_pass']}),flush=True)
