"""Independent controls for state mobility and explicit initial composition."""
import csv
import importlib.util
import itertools
from pathlib import Path
import numpy as np
import experiment as model


def test_default_dynamics_matches_frozen_v01_bytes(tmp_path):
    source=Path(__file__).resolve().parent.parent/'20261108-local-reactive-lattice/experiment.py'
    loader=importlib.util.spec_from_file_location('_frozen_v01_reference',source)
    old=importlib.util.module_from_spec(loader);loader.loader.exec_module(old)
    case={'id':'same_law','mu':2.,'df':1.2}
    a=old.run(tmp_path/'old','validation',case,n=6,d=3,T=20.,seed=101)
    b=model.run(tmp_path/'new','validation',case,n=6,d=3,T=20.,seed=101)
    for suffix in ['cells','positions','conformers','displacements']:
        assert (a/f'state-2-{suffix}.bin').read_bytes()==(b/f'state-2-{suffix}.bin').read_bytes()
    assert (a/'series.csv').read_bytes()==(b/'series.csv').read_bytes()


def test_unequal_diffusivities_preserve_exact_canonical_distribution(tmp_path):
    n,d,eps,df=3,3,-.7,.3;expected={}
    for i in range(n**d):
        x=np.array(np.unravel_index(i,(n,)*d,order='F'))
        for j in range(i+1,n**d):
            y=np.array(np.unravel_index(j,(n,)*d,order='F'));delta=np.minimum(abs(x-y),n-abs(x-y));adjacent=delta.sum()==1
            for a,b in itertools.product([0,1],repeat=2):
                key=(a+b,int(adjacent and a and b));expected[key]=expected.get(key,0.)+np.exp(-df*key[0]-eps*key[1])
    Z=sum(expected.values());expected={k:v/Z for k,v in expected.items()}
    path=model.run(tmp_path,'validation',{'id':'unequal','mu':0.,'df':df,'epsilon':eps,'D':1.,'D_I':7.},n=n,d=d,T=30000.,seed=833,molecules=2,scheduler=1)
    rows=list(csv.DictReader((path/'series.csv').open()))[300:]
    actual={k:sum((int(r['B']),int(r['pairs']))==k for r in rows)/len(rows) for k in expected}
    assert max(abs(actual[k]-expected[k]) for k in expected)<.05,(actual,expected)


def test_each_frozen_conformation_has_its_own_poisson_hop_clock(tmp_path):
    for fraction,coefficient in [(0.,7.),(1.,1.)]:
        path=model.run(tmp_path,'validation',{'id':f'walker{fraction}','epsilon':0.,'D':1.,'D_I':7.,'rate':0.,'initial_B_fraction':fraction},n=5,d=3,T=10000.,seed=919,molecules=1,scheduler=1)
        rows=list(csv.DictReader((path/'series.csv').open()));hops=int(rows[-1]['hops']);mean=coefficient*10000
        assert abs(hops-mean)<5*np.sqrt(mean)
        assert all(int(r['B'])==int(fraction) for r in rows)


def test_frozen_population_is_an_input_and_stays_conserved(tmp_path):
    for fraction in [.995,.872]:
        path=model.run(tmp_path,'validation',{'id':f'population{fraction}','rate':0.,'initial_B_fraction':fraction,'D_I':1.},n=8,d=3,T=100.,seed=93,scheduler=1)
        rows=list(csv.DictReader((path/'series.csv').open()));M=int(rows[0]['molecules'])
        assert all(int(r['B'])==int(M*fraction) and int(r['molecules'])==M for r in rows)
        assert all(float(r['work'])==0 for r in rows)


def test_driven_type_bound_ledger_and_complete_state_determinism(tmp_path):
    paths=[model.run(tmp_path,'validation',{'id':f'driven{i}','df':2.4,'D_I':1.},n=8,d=3,T=100.,seed=319,scheduler=1) for i in range(2)]
    assert (paths[0]/'series.csv').read_bytes()==(paths[1]/'series.csv').read_bytes()
    for suffix in ['cells','positions','conformers','displacements']:
        assert (paths[0]/f'state-10-{suffix}.bin').read_bytes()==(paths[1]/f'state-10-{suffix}.bin').read_bytes()
    rows=list(csv.DictReader((paths[0]/'series.csv').open()))
    assert float(rows[-1]['work'])>0
    for r in rows:assert np.isclose(float(r['heat']),float(r['work'])-float(r['H'])+float(rows[0]['H']),rtol=1e-12,atol=1e-9)
