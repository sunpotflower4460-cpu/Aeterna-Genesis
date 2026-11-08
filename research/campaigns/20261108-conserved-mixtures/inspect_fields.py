"""Read-only diagnostics of saved full-precision fields. No physics writes.

Component energy is defined as self energy plus HALF the cross energy; its
exchange is antisymmetric and the two parts add to the conserved Hamiltonian.
Density superlevel sets are field concentrations, not membranes or organisms.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from scipy import ndimage
import run as campaign
from genesis.diagnostics.vessel_geometry_3d import _merge_periodic_labels

def inspect(path):
    path=Path(path);recipe=json.loads((path/'recipe.json').read_text())
    n,d=recipe['grid'],recipe['dimension'];h=recipe['length']/n
    g=recipe['g'];convex=recipe['control']=='convex'
    records=[]
    original={r['file']:r for r in json.loads((path/'summary.json').read_text())['frames']}
    for frame in sorted(path.glob('state-*.bin'),key=lambda p:int(p.stem.split('-')[1])):
        assert campaign.sha(frame)==original[frame.name]['sha256']
        u=np.fromfile(frame).reshape((8,)+(n,)*d)
        if not np.isfinite(u).all():
            records.append({'file':frame.name,'finite':False});continue
        z=[u[0]+1j*u[1],u[2]+1j*u[3]]
        p=[u[4]+1j*u[5],u[6]+1j*u[7]]
        s=[np.abs(x)**2 for x in z]
        q=[2*np.imag(np.conj(a)*b) for a,b in zip(z,p)]
        self_energy=[]
        for a,b,den in zip(z,p,s):
            V=(.025*den+.01*den**2) if convex else (.02*den*(den-1)**2+.005*den)
            grad=sum(np.abs(np.roll(a,-1,ax)-a)**2/h**2 for ax in range(d))
            self_energy.append(np.abs(b)**2+grad+V)
        cross=g*s[0]*s[1]
        energies=[float(np.mean(v+.5*cross)) for v in self_energy]
        sectors=[]
        for a,den,charge in zip(z,s,q):
            lbl,count=ndimage.label(den>2*den.mean())
            lbl=_merge_periodic_labels(lbl,den>2*den.mean())
            labels=np.unique(lbl);labels=labels[labels>0]
            regions=[]
            for label in labels:
                mask=lbl==label
                regions.append({'voxels':int(mask.sum()),'physical_volume':float(mask.sum()*h**d),
                    'signed_charge':float(charge[mask].sum()*h**d),
                    'absolute_charge':float(np.abs(charge[mask]).sum()*h**d),
                    'charge_sign_coherence':float(abs(charge[mask].sum())/max(np.abs(charge[mask]).sum(),1e-30)),
                    'charge_weighted_rotation':float(charge[mask].sum()/max(2*den[mask].sum(),1e-30))})
            regions.sort(key=lambda r:r['voxels'],reverse=True)
            kh=np.fft.fftfreq(n)*2*np.pi
            modes=np.meshgrid(*([kh]*d),indexing='ij')
            klat=sum(4*np.sin(k/2)**2/h**2 for k in modes)
            power=np.abs(np.fft.fftn(a))**2*klat
            high=sum(k*k for k in modes)>(.7*np.pi)**2
            sectors.append({'high_k_gradient_energy_fraction':float(power[high].sum()/max(power.sum(),1e-30)),
                'z_resolved_variance_fraction':float(np.var(den-den.mean(axis=-1,keepdims=True))/max(np.var(den),1e-30)),
                'total_signed_charge':float(charge.sum()*h**d),
                'total_absolute_charge':float(np.abs(charge).sum()*h**d),
                'regions_at_twice_mean':regions})
        records.append({'file':frame.name,'time':int(frame.stem.split('-')[1])*recipe['dt'],
                        'energy_density_by_sector':energies,'interaction_energy_density':float(cross.mean()),
                        'density_mean':[float(x.mean()) for x in s], 'sectors':sectors})
    E0=records[0]['energy_density_by_sector'];E1=records[-1]['energy_density_by_sector']
    return {'run':path.name,'role':'read-only exploratory diagnostic; no new qualification gate',
            'sector_energy_change_as_fraction_of_total':[(b-a)/sum(E0) for a,b in zip(E0,E1)],'frames':records}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--stage',default='discovery');p.add_argument('--out',required=True)
    a=p.parse_args();out=Path(a.out)
    if out.exists():raise FileExistsError(out)
    result={}
    for path in sorted((Path(a.root)/a.stage).glob('*/summary.json')):
        v=inspect(path.parent);result[path.parent.name]=v
        final=v['frames'][-1]
        print(json.dumps({'run':path.parent.name,'energy_exchange':v['sector_energy_change_as_fraction_of_total'],
            'largest_region_charge_coherence':[s['regions_at_twice_mean'][0]['charge_sign_coherence'] if s['regions_at_twice_mean'] else None for s in final['sectors']],
            'high_k':[s['high_k_gradient_energy_fraction'] for s in final['sectors']]}),flush=True)
    campaign.save(out,result)
