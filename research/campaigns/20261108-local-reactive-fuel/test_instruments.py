"""Known exact open/closed thermodynamic controls, never research discoveries."""
import csv
import io
import itertools
import subprocess
import numpy as np
import pytest
import experiment as model


def canonical(n,d,epsilon,df):
    weights={}
    for i in range(n**d):
        x=np.array(np.unravel_index(i,(n,)*d,order='F'))
        for j in range(i+1,n**d):
            y=np.array(np.unravel_index(j,(n,)*d,order='F'));delta=np.minimum(abs(x-y),n-abs(x-y));adj=delta.sum()==1
            for a,b in itertools.product([0,1],repeat=2):
                k=(a+b,int(adj and a and b));weights[k]=weights.get(k,0.)+np.exp(-df*k[0]-epsilon*k[1])
    Z=sum(weights.values());return {k:v/Z for k,v in weights.items()}


def test_each_elementary_pair_has_its_physical_reverse_rate():
    e,f,p,h=-.7,.3,.8,2.4
    output=subprocess.check_output([str(model.binary()),'--rates',str(e),str(f),str(p),str(h),'3'],text=True)
    for row in csv.DictReader(io.StringIO(output)):
        n=int(row['n']);expected=f+e*n
        assert np.isclose(np.log(float(row['bp'])/float(row['ip'])),expected,rtol=0,atol=1e-15)
        assert np.isclose(np.log(float(row['bd_pair'])/float(row['id_pair'])),expected,rtol=0,atol=1e-15)


def test_exact_3d_grand_canonical_macro_and_fuel_distributions(tmp_path):
    for name,mu,passive,source in [('equal',0.,1.,'plane'),('single_path',1.,0.,'uniform')]:
        case={'id':name,'epsilon':-.7,'df':.3,'eta':2.,'passive_rate':passive,'mu':mu,'D_B':2.,'D_I':2.,'D_F':4.,'D_W':4.,'kex':3.,'source':source}
        path=model.run(tmp_path,'validation',case,n=3,d=3,T=50000.,seed=902,molecules=2)
        rows=list(csv.DictReader((path/'series.csv').open()))[500:]
        expected=canonical(3,3,-.7,.3+(mu if passive==0 else 0))
        actual={k:sum((int(r['B']),int(r['pairs']))==k for r in rows)/len(rows) for k in expected}
        assert max(abs(expected[k]-actual[k]) for k in expected)<.05,(name,expected,actual)
        F=np.array([int(r['F']) for r in rows]);W=np.array([int(r['W']) for r in rows])
        zF=.25/(1+np.exp(-mu));zW=.25/(1+np.exp(mu))
        assert abs(F.mean()-25*zF/1.25)<.2
        assert abs(W.mean()-25*zW/1.25)<.2
        assert abs((F+W).var()-25*.2*.8)<.8
        # In both equilibrium controls, source work is bounded by endpoint state
        # changes, not sustained chemical cycling.
        start=rows[0]
        for r in rows:
            predicted=np.log(zF)*(int(r['F'])-int(start['F']))+np.log(zW)*(int(r['W'])-int(start['W']))
            if passive==0:predicted-=mu*(int(r['B'])-int(start['B']))
            assert np.isclose(float(r['work'])-float(start['work']),predicted,rtol=1e-11,atol=2e-8)


def test_closed_stoichiometry_has_finite_fuel_and_zero_external_work(tmp_path):
    for mu in [-4.,4.]:
        path=model.run(tmp_path,'validation',{'id':f'closed{mu}','mu':mu,'source':'closed'},n=6,d=3,T=100.,seed=619)
        rows=list(csv.DictReader((path/'series.csv').open()));F0,W0=int(rows[0]['F']),int(rows[0]['W'])
        for r in rows:
            net=sum(int(r[f'rxn_2_{n}'])-int(r[f'rxn_3_{n}']) for n in range(7))
            assert int(r['F'])==F0-net and int(r['W'])==W0+net
            assert float(r['work'])==0
            assert all(int(r[k])==0 for k in ['F_in','F_out','W_in','W_out'])


def test_full_state_determinism_and_matched_unstructured_initial_conditions(tmp_path):
    cases=[{'id':'a'},{'id':'b'},{'id':'closed','source':'closed'},{'id':'slow','D_F':1.,'D_W':1.}]
    paths=[model.run(tmp_path,'validation',c,n=6,d=3,T=30.,seed=171) for c in cases]
    assert (paths[0]/'series.csv').read_bytes()==(paths[1]/'series.csv').read_bytes()
    for kind in ['cells','positions','conformers','displacements']:
        assert (paths[0]/f'state-3-{kind}.bin').read_bytes()==(paths[1]/f'state-3-{kind}.bin').read_bytes()
        assert len({(p/f'state-0-{kind}.bin').read_bytes() for p in paths})==1


def test_existing_history_is_protected(tmp_path):
    case={'id':'protect'};path=model.run(tmp_path,'validation',case,n=4,d=3,T=10.,seed=7)
    before=model.digest(path/'series.csv')
    with pytest.raises(FileExistsError):model.run(tmp_path,'validation',case,n=4,d=3,T=10.,seed=7)
    assert model.digest(path/'series.csv')==before
