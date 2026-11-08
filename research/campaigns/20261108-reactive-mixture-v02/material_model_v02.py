"""Bounded material constitutive hypothesis (a different white from v01).

Adds positive, stoichiometric excluded-volume pressure eta*n^2/2. Reaction
conserves n locally so this term cancels from reaction affinity. Transport
uses its chemical-potential gradient and preserves all building blocks.
No boundary shape, protection rule, permeability mask or biological gate.
"""
import importlib.util
from pathlib import Path
import numpy as np

BASE_PATH=Path(__file__).resolve().parent.parent/'20261108-reactive-mixture'/'material_model.py'
loader=importlib.util.spec_from_file_location('_validated_material_base',BASE_PATH)
base=importlib.util.module_from_spec(loader);loader.loader.exec_module(base)
digest=base.digest

class Solver(base.Solver):
    def __init__(self,*args,eta=.1,**kwargs):
        if eta<=0:raise ValueError('positive excluded-volume pressure is required in v02')
        self.eta=eta;self.transport_rejections=0;self.minimum_transport_step=float('inf')
        super().__init__(*args,**kwargs)

    def free_energy(self,phi,c):
        n=c[0]+c[1]+2*c[2]
        return super().free_energy(phi,c)+float(.5*self.eta*np.mean(n*n))

    def transport(self,phi,c,duration):
        # IMEX: nonideal potential is lagged over a numerical substep, ideal
        # diffusion is implicit. Rejected numerical trials never replace state.
        # Error control uses the thermodynamic Lyapunov law, never geometry.
        remain=duration;h=duration
        axes=list(range(self.d-1))+[self.d-1]+list(range(self.d-2,-1,-1))
        while remain>duration*1e-12:
            h=min(h,remain);oldE=self.free_energy(phi,c)
            n=c[0]+c[1]+2*c[2]
            per_block=np.ascontiguousarray(self.eta*n-self.chi*phi)
            candidate=c.copy();valid=True
            for axis in axes:
                dt=h if axis==self.d-1 else h/2
                for i,valence in enumerate([1.,1.,2.]):
                    code=self.lib.transport_axis(candidate[i],per_block,self.n,self.d,axis,-1.,valence,self.D,dt,self.dx)
                    valid=valid and code==0
            newE=self.free_energy(phi,candidate) if valid and candidate.min()>0 else float('inf')
            if not np.isfinite(newE) or newE>oldE+1e-12*max(1.,abs(oldE)):
                h*=.5;self.transport_rejections+=1
                if h<1e-10:raise FloatingPointError('nonideal transport failed numerical Lyapunov control')
                continue
            self.minimum_transport_step=min(self.minimum_transport_step,h)
            c=candidate;remain-=h
        return c

    def step(self,phi,c,dt):
        phi=self.phase_advance(phi,c,dt/2)
        c=base.reaction(c,dt/2,self.K,self.rate)
        c=self.transport(phi,c,dt)
        c=base.reaction(c,dt/2,self.K,self.rate)
        phi=self.phase_advance(phi,c,dt/2)
        return phi,c

    def explicit_rhs(self,phi,c):
        """Independent local finite-volume validator of the same material law."""
        def lap(x):return sum(np.roll(x,1,a)+np.roll(x,-1,a)-2*x for a in range(self.d))/self.dx**2
        n=c[0]+c[1]+2*c[2]
        mu=self.alpha*phi+self.beta*phi**3-self.kappa*lap(phi)-self.chi*n
        dphi=self.M*lap(mu);dc=np.zeros_like(c)
        def B(x):
            out=np.empty_like(x);small=np.abs(x)<1e-6
            out[small]=1-x[small]/2+x[small]**2/12
            out[~small]=x[~small]/np.expm1(x[~small]);return out
        for i,valence in enumerate([1.,1.,2.]):
            psi=valence*(self.eta*n-self.chi*phi)
            for axis in range(self.d):
                jump=np.roll(psi,-1,axis)-psi
                flux=self.D/self.dx*(B(jump)*c[i]-B(-jump)*np.roll(c[i],-1,axis))
                dc[i]-=(flux-np.roll(flux,1,axis))/self.dx
        R=.02*self.rate*(self.K*c[0]*c[1]-c[2]);dc[0]-=R;dc[1]-=R;dc[2]+=R
        return dphi,dc
