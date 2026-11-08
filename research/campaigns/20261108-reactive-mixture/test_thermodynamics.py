"""Known-law and numerical validation, never counted as new discoveries."""
import numpy as np
from material_model import Solver,reaction

def test_cyclic_solver_matches_independent_dense_matrix():
    n=9;rng=np.random.default_rng(1)
    phi=rng.normal(0,.2,n);c=rng.uniform(.1,1,n);old=c.copy()
    solver=Solver((n,),n,chi=.7,D=1.)
    dt=.8;psi=-2*.7*phi
    def B(x):return x/np.expm1(x)
    A=np.eye(n)
    for i in range(n):
        j=(i+1)%n;v=psi[j]-psi[i];f,b=B(v),B(-v)
        A[i,i]+=dt*f;A[j,i]-=dt*f;A[i,j]-=dt*b;A[j,j]+=dt*b
    solver.diffuse_axis(c,phi,0,dt,2.)
    assert np.max(np.abs(c-np.linalg.solve(A,old)))<2e-15
    assert abs(c.sum()-old.sum())<2e-14

def test_boltzmann_equilibrium_is_preserved_at_arbitrary_step():
    rng=np.random.default_rng(2);phi=rng.normal(0,.3,(8,8,8))
    solver=Solver(phi.shape,8,chi=.8)
    for valence in [1.,2.]:
        c=np.exp(valence*.8*phi);old=c.copy()
        for axis in range(3):solver.diffuse_axis(c,phi,axis,13.,valence)
        assert np.max(np.abs(c-old))<5e-13

def test_fourier_diffusion_eigenvalue_and_no_negative_concentration():
    n=12;x=np.arange(n);old=1+.1*np.cos(2*np.pi*x/n)
    phi=np.zeros((n,n,n));c=np.broadcast_to(old[:,None,None],phi.shape).copy()
    solver=Solver(phi.shape,n,chi=0.,D=5.);dt=2.
    solver.diffuse_axis(c,phi,2,dt,1.)
    expected=1+.1*np.cos(2*np.pi*x/n)/(1+dt*5*4*np.sin(np.pi/n)**2)
    assert np.max(np.abs(c-expected[:,None,None]))<3e-14
    assert c.min()>0

def test_exact_reaction_conserves_both_atoms_and_lowers_free_energy():
    rng=np.random.default_rng(3);c=rng.uniform(.01,2,(3,8,8,8))
    for K in [.01,10.,100.]:
        for dt in [.01,1.,10000.]:
            out=reaction(c,dt,K,1.)
            assert np.max(np.abs(out[0]+out[2]-c[0]-c[2]))<9e-16
            assert np.max(np.abs(out[1]+out[2]-c[1]-c[2]))<9e-16
            def F(v):return np.sum(v*(np.log(v)-1))-np.log(K)*v[2].sum()
            assert out.min()>0
            assert F(out)<=F(c)+1e-10

def test_full_step_mass_and_free_energy_budget():
    rng=np.random.default_rng(4);phi=rng.normal(0,.02,(8,8,8));c=rng.uniform(.05,.5,(3,8,8,8))
    solver=Solver(phi.shape,8)
    atoms=[float((c[0]+c[2]).sum()),float((c[1]+c[2]).sum())];p0=phi.mean()
    E=solver.free_energy(phi,c)
    for _ in range(12):
        phi,c=solver.step(phi,c,.25);newE=solver.free_energy(phi,c)
        assert newE<=E+1e-11;E=newE
    assert abs((c[0]+c[2]).sum()-atoms[0])<1e-10
    assert abs((c[1]+c[2]).sum()-atoms[1])<1e-10
    assert abs(phi.mean()-p0)<2e-15

def test_implicit_step_has_the_independent_local_limit():
    rng=np.random.default_rng(5);phi=rng.normal(0,.01,(6,6,6));c=rng.uniform(.1,.5,(3,6,6,6))
    solver=Solver(phi.shape,6)
    fp,fc=solver.explicit_rhs(phi,c)
    errors=[]
    for dt in [1e-4,5e-5]:
        pnew,cnew=solver.step(phi.copy(),c.copy(),dt)
        errors.append(np.linalg.norm(pnew-phi-dt*fp)+np.linalg.norm(cnew-c-dt*fc))
    assert errors[0]/errors[1]>3.8
