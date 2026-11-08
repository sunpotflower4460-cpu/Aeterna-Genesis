"""Known statistical-mechanical checks, excluded from the discovery count."""
import csv
import io
import itertools
import subprocess
import numpy as np
import pytest
import experiment as model


def exact_two_molecule_distribution(n,d,eps,df):
    V=n**d;distribution={}
    for i in range(V):
        ci=np.array(np.unravel_index(i,(n,)*d,order='F'))
        for j in range(i+1,V):
            cj=np.array(np.unravel_index(j,(n,)*d,order='F'))
            delta=np.minimum(np.abs(ci-cj),n-np.abs(ci-cj))
            adjacent=delta.sum()==1
            for a,b in itertools.product([0,1],repeat=2):
                key=(a+b,int(adjacent and a and b))
                distribution[key]=distribution.get(key,0.)+np.exp(-df*key[0]-eps*key[1])
    total=sum(distribution.values())
    return {key:value/total for key,value in distribution.items()}


def test_every_local_rate_obeys_the_separate_thermodynamic_ratio():
    e,f,mu,eta,ts,D,rate=-.65,.4,1.7,.73,.37,4.,.8
    output=subprocess.check_output([str(model.binary()),'--rates',*[str(x) for x in [e,f,mu,eta,ts,D,rate,3]]],text=True)
    for row in csv.DictReader(io.StringIO(output)):
        n=int(row['n']);bp,ip,bd,ib=[float(row[k]) for k in ['bp','ip','bd','id']]
        assert np.isclose(np.log(bp/ip),f+e*n,rtol=0,atol=8e-16)
        assert np.isclose(np.log(bd/ib),f+e*n+mu,rtol=0,atol=8e-16)
        assert float(row['pbar'])>=max(bp,ip) and float(row['dbar'])>=max(bd,ib)


def test_three_dimensional_canonical_distribution_then_2d_and_common_saddle(tmp_path):
    for d in [3,2]:
        for name,extra,effective in [
            ('passive',{'eta':0.},.3),
            ('two_paths',{'eta':1.,'mu':0.,'ts_fraction':.5},.3),
            ('common_saddle',{'eta':1.,'mu':2.,'ts_fraction':0.},1.3),
        ]:
            case={'id':name,'epsilon':-.7,'df':.3,'D':2.}|extra
            path=model.run(tmp_path,'validation',case,n=3,d=d,T=50000.,seed=800+d,molecules=2)
            rows=list(csv.DictReader((path/'series.csv').open()))[500:]
            expected=exact_two_molecule_distribution(3,d,-.7,effective)
            observed={k:sum((int(r['B']),int(r['pairs']))==k for r in rows)/len(rows) for k in expected}
            assert max(abs(expected[k]-observed[k]) for k in expected)<.04,(d,name,expected,observed)


def test_unwrapped_single_particle_walk_has_independent_poisson_statistics(tmp_path):
    D=5.;T=100000.
    path=model.run(tmp_path,'validation',{'id':'walker','epsilon':0.,'D':D,'mu':2.},n=5,d=3,T=T,seed=991,molecules=1)
    rows=list(csv.DictReader((path/'series.csv').open()))
    hops=int(rows[-1]['hops'])
    assert abs(hops-D*T)<5*np.sqrt(D*T)
    positions=np.array([[float(r[f'mean_dx{a}']) for a in range(3)] for r in rows])
    increments=np.diff(positions,axis=0)
    msd=np.mean(np.sum(increments**2,axis=1))
    assert abs(msd/(D*10)-1)<.05
    for a in range(3):assert abs(np.mean(increments[:,a]**2)/(D*10/3)-1)<.1


def test_complete_state_determinism_and_matched_initial_conditions(tmp_path):
    cases=[{'id':'repeat_a','mu':2.},{'id':'repeat_b','mu':2.},{'id':'other_environment','mu':-2.}]
    paths=[model.run(tmp_path,'validation',c,n=6,d=3,T=20.,seed=101) for c in cases]
    for suffix in ['cells','positions','conformers','displacements']:
        assert (paths[0]/f'state-2-{suffix}.bin').read_bytes()==(paths[1]/f'state-2-{suffix}.bin').read_bytes()
        assert (paths[0]/f'state-0-{suffix}.bin').read_bytes()==(paths[2]/f'state-0-{suffix}.bin').read_bytes()
    assert (paths[0]/'series.csv').read_bytes()==(paths[1]/'series.csv').read_bytes()


def test_energy_accounting_pair_cache_and_frozen_reaction(tmp_path):
    for case in [{'id':'plus','mu':2.},{'id':'minus','mu':-2.},{'id':'frozen','rate':0.}]:
        path=model.run(tmp_path,'validation',case,n=8,d=3,T=100.,seed=83)
        rows=list(csv.DictReader((path/'series.csv').open()))
        for r in rows:
            work=float(r['work']);delta=float(r['H'])-float(rows[0]['H'])
            assert np.isclose(float(r['heat']),work-delta,rtol=1e-12,atol=1e-9)
        if case['id']=='frozen':
            assert len({r['B'] for r in rows})==1
            assert float(rows[-1]['work'])==0
            assert all(int(rows[-1][k])==0 for k in rows[-1] if k.startswith('rxn_'))


def test_existing_output_is_never_overwritten(tmp_path):
    case={'id':'protect'};path=model.run(tmp_path,'validation',case,n=4,d=3,T=10.,seed=9)
    before=model.digest(path/'series.csv')
    with pytest.raises(FileExistsError):model.run(tmp_path,'validation',case,n=4,d=3,T=10.,seed=9)
    assert model.digest(path/'series.csv')==before
