"""Isothermal, reciprocal reaction/transport material model; no objects or masks.

Constitutive hypothesis, not an identified molecular liquid. All atom blocks and
material are conserved. Free energy decreases into a declared heat bath. Implicit
line/Fourier solves are disclosed numerical shortcuts, not strict local updates.
"""
from __future__ import annotations
import ctypes
import hashlib
from pathlib import Path
import subprocess
import numpy as np
from scipy.fft import rfftn, irfftn

HERE=Path(__file__).resolve().parent

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def library():
    source=HERE/'implicit_transport.cpp'
    path=Path('/tmp')/('aeterna-material-'+digest(source)[:16]+'.so')
    if not path.exists():
        subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC','-fopenmp',str(source),'-o',str(path)],check=True)
    lib=ctypes.CDLL(str(path));pointer=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    lib.transport_axis.argtypes=[pointer,pointer,ctypes.c_int,ctypes.c_int,ctypes.c_int,
                                ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_double]
    lib.transport_axis.restype=ctypes.c_int
    return lib

def reaction(c,dt,K,rate):
    if rate==0:return c.copy()
    kf,kr=.02*K*rate,.02*rate
    a,b,z=c
    A,B=a+z,b+z
    S=kf*(A+B)+kr
    gap=np.sqrt(S*S-4*kf*kf*A*B)/kf
    low=2*kf*A*B/(S+kf*gap)
    delta=z-low
    decay=np.exp(-kf*gap*dt)
    znew=low+delta*decay/(1-delta/gap*(1-decay))
    extent=znew-z
    out=np.stack([a-extent,b-extent,znew])
    if not np.isfinite(out).all() or np.min(out)<=0:raise FloatingPointError('invalid concentration; never clipped')
    return out

class Solver:
    def __init__(self,shape,L,chi=1.,K=10.,rate=1.,alpha=1.,beta=4.,kappa=2.,M=1.,D=5.):
        self.shape=tuple(shape);self.n=shape[0];self.d=len(shape);self.dx=L/self.n
        self.chi,self.K,self.rate=chi,K,rate
        self.alpha,self.beta,self.kappa,self.M,self.D=alpha,beta,kappa,M,D
        modes=[np.fft.fftfreq(n) if a<self.d-1 else np.fft.rfftfreq(n) for a,n in enumerate(shape)]
        grids=np.meshgrid(*modes,indexing='ij')
        self.k2=sum(4*np.sin(np.pi*k)**2/self.dx**2 for k in grids)
        self.lib=library();self.phase_rejections=0;self.minimum_phase_step=float('inf')

    def phase_energy(self,phi,c):
        n=c[0]+c[1]+2*c[2]
        local=.5*self.alpha*phi**2+.25*self.beta*phi**4-self.chi*phi*n
        local=local+.5*self.kappa*sum((np.roll(phi,-1,axis)-phi)**2/self.dx**2 for axis in range(self.d))
        return float(local.mean())

    def free_energy(self,phi,c):
        if not np.isfinite(c).all() or np.min(c)<=0:raise FloatingPointError('log chemical potential requires positive concentrations')
        ideal=np.sum(c*(np.log(c)-1),axis=0)-np.log(self.K)*c[2]
        return self.phase_energy(phi,c)+float(ideal.mean())

    def phase_advance(self,phi,c,duration):
        # Adapt only to the known Lyapunov property of this gradient-flow
        # integrator, never to geometry, growth, or a research success criterion.
        remain=duration;h=duration
        while remain>duration*1e-12:
            h=min(h,remain);oldE=self.phase_energy(phi,c)
            nonlin=self.beta*phi**3-self.chi*(c[0]+c[1]+2*c[2])
            candidate=irfftn((rfftn(phi)-h*self.M*self.k2*rfftn(nonlin))/
                            (1+h*self.M*self.k2*(self.alpha+self.kappa*self.k2)),s=self.shape)
            newE=self.phase_energy(candidate,c)
            if not np.isfinite(newE) or newE>oldE+1e-12*max(1.,abs(oldE)):
                h*=.5;self.phase_rejections+=1
                if h<1e-10:raise FloatingPointError('phase integration failed Lyapunov check')
                continue
            self.minimum_phase_step=min(self.minimum_phase_step,h)
            phi=np.ascontiguousarray(candidate);remain-=h
        return phi

    def diffuse_axis(self,c,phi,axis,dt,valence):
        code=self.lib.transport_axis(c,phi,self.n,self.d,axis,self.chi,valence,self.D,dt,self.dx)
        if code:raise FloatingPointError(f'SG implicit solve failed ({code}); state is not clipped')

    def step(self,phi,c,dt):
        phi=self.phase_advance(phi,c,dt/2)
        c=reaction(c,dt/2,self.K,self.rate)
        axes=list(range(self.d-1))+[self.d-1]+list(range(self.d-2,-1,-1))
        for axis in axes:
            sub=dt if axis==self.d-1 else dt/2
            for i,valence in enumerate([1.,1.,2.]):self.diffuse_axis(c[i],phi,axis,sub,valence)
        c=reaction(c,dt/2,self.K,self.rate)
        phi=self.phase_advance(phi,c,dt/2)
        return phi,c

    def explicit_rhs(self,phi,c):
        """Independent local short-time validator, no implicit/Fourier inversions."""
        def lap(x):return sum(np.roll(x,1,a)+np.roll(x,-1,a)-2*x for a in range(self.d))/self.dx**2
        mu=self.alpha*phi+self.beta*phi**3-self.kappa*lap(phi)-self.chi*(c[0]+c[1]+2*c[2])
        dphi=self.M*lap(mu)
        dc=np.zeros_like(c)
        def B(x):
            out=np.empty_like(x);small=np.abs(x)<1e-6
            out[small]=1-x[small]/2+x[small]**2/12
            out[~small]=x[~small]/np.expm1(x[~small])
            return out
        for i,valence in enumerate([1.,1.,2.]):
            psi=-valence*self.chi*phi
            for axis in range(self.d):
                jump=np.roll(psi,-1,axis)-psi
                flux=self.D/self.dx*(B(jump)*c[i]-B(-jump)*np.roll(c[i],-1,axis))
                dc[i]-=(flux-np.roll(flux,1,axis))/self.dx
        R=.02*self.rate*(self.K*c[0]*c[1]-c[2])
        dc[0]-=R;dc[1]-=R;dc[2]+=R
        return dphi,dc
