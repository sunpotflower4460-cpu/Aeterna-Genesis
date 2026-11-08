"""Independent known-law checks for v02, not new physical findings."""
import numpy as np
from material_model_v02 import Solver,base

def test_excluded_volume_does_not_change_local_reaction_stoichiometry_or_affinity():
    rng=np.random.default_rng(1);c=rng.uniform(.1,1,(3,6,6,6));phi=rng.normal(0,.1,(6,6,6))
    solver=Solver(phi.shape,6,eta=.25)
    E=solver.free_energy(phi,c);new=base.reaction(c,20,10,1)
    assert solver.free_energy(phi,new)<=E
    assert np.max(np.abs(c[0]+c[2]-new[0]-new[2]))<1e-15
    assert np.max(np.abs(c[1]+c[2]-new[1]-new[2]))<1e-15

def test_nonlinear_transport_preserves_nonideal_equilibrium():
    rng=np.random.default_rng(2);phi=rng.normal(0,.2,(6,6,6))
    solver=Solver(phi.shape,6,chi=1.,eta=.25)
    low=np.zeros_like(phi);high=np.ones_like(phi)*20
    for _ in range(80):
        n=(low+high)/2;s=phi-.25*n
        rhs=.4*np.exp(s)+.2*np.exp(2*s)
        low=np.where(n<rhs,n,low);high=np.where(n>=rhs,n,high)
    n=(low+high)/2;s=phi-.25*n
    c=np.stack([.2*np.exp(s),.2*np.exp(s),.1*np.exp(2*s)])
    new=solver.transport(phi,c,5.)
    assert np.max(np.abs(new-c))<1e-12

def test_full_step_keeps_all_atoms_positive_and_lowers_free_energy():
    rng=np.random.default_rng(3);phi=rng.normal(0,.02,(8,8,8));c=rng.uniform(.1,.8,(3,8,8,8))
    solver=Solver(phi.shape,8,eta=.25)
    atoms=[(c[i]+c[2]).sum() for i in range(2)];p0=phi.mean();E=solver.free_energy(phi,c)
    for _ in range(10):
        phi,c=solver.step(phi,c,.5);nextE=solver.free_energy(phi,c)
        assert nextE<=E+1e-10;E=nextE
        assert c.min()>0
    assert max(abs((c[i]+c[2]).sum()-atoms[i]) for i in range(2))<1e-10
    assert abs(phi.mean()-p0)<1e-14

def test_exact_monomer_symmetry_is_not_numerically_broken():
    rng=np.random.default_rng(4);phi=rng.normal(0,.02,(6,6,6));c=rng.uniform(.1,.5,(3,6,6,6));c[1]=c[0]
    solver=Solver(phi.shape,6)
    for _ in range(6):phi,c=solver.step(phi,c,.25)
    assert np.array_equal(c[0],c[1])

def test_small_step_matches_independent_local_flux_law():
    rng=np.random.default_rng(5);phi=rng.normal(0,.01,(6,6,6));c=rng.uniform(.1,.5,(3,6,6,6))
    solver=Solver(phi.shape,6,eta=.25)
    fp,fc=solver.explicit_rhs(phi,c);errors=[]
    for dt in [1e-4,5e-5]:
        pnew,cnew=solver.step(phi.copy(),c.copy(),dt)
        errors.append(np.linalg.norm(pnew-phi-dt*fp)+np.linalg.norm(cnew-c-dt*fc))
    assert errors[0]/errors[1]>3.8

def test_step_refinement_approaches_explicit_local_history():
    rng=np.random.default_rng(6);p=rng.normal(0,.005,(4,4,4));c=rng.uniform(.1,.3,(3,4,4,4))
    solver=Solver(p.shape,4,eta=.25);pref,cref=p.copy(),c.copy();T=.005
    for _ in range(1000):
        fp,fc=solver.explicit_rhs(pref,cref);pref+=T/1000*fp;cref+=T/1000*fc
    errors=[]
    for dt in [.0005,.00025]:
        pp,cc=p.copy(),c.copy()
        for _ in range(round(T/dt)):pp,cc=solver.step(pp,cc,dt)
        errors.append(np.linalg.norm(pp-pref)+np.linalg.norm(cc-cref))
    assert errors[0]/errors[1]>1.7

def test_same_seed_repeats_the_complete_material_state_exactly():
    def history(seed):
        rng=np.random.default_rng(seed)
        phi=rng.normal(0,.02,(8,8,8));c=rng.uniform(.1,.8,(3,8,8,8))
        solver=Solver(phi.shape,8)
        for _ in range(10):phi,c=solver.step(phi,c,.25)
        return phi,c,solver.phase_rejections,solver.transport_rejections
    first,second=history(71),history(71)
    assert np.array_equal(first[0],second[0])
    assert np.array_equal(first[1],second[1])
    assert first[2:]==second[2:]
