"""Independent equilibrium and absolute-clock checks of the exact sparse proposal."""
import csv
import numpy as np
import experiment_sparse as model
from test_instruments import canonical


def test_sparse_grand_canonical_and_single_path_controls(tmp_path):
    for name,mu,passive,source in [('equal',0.,1.,'plane'),('single',1.,0.,'uniform')]:
        case={'id':name,'epsilon':-.7,'df':.3,'eta':2.,'passive_rate':passive,'mu':mu,'D_B':2.,'D_I':2.,'D_F':4.,'D_W':4.,'kex':3.,'source':source}
        path=model.run(tmp_path,'validation',case,n=3,d=3,T=30000.,seed=909,molecules=2)
        rows=list(csv.DictReader((path/'series.csv').open()))[300:]
        expected=canonical(3,3,-.7,.3+(mu if passive==0 else 0))
        actual={k:sum((int(r['B']),int(r['pairs']))==k for r in rows)/len(rows) for k in expected}
        assert max(abs(expected[k]-actual[k]) for k in expected)<.05,(expected,actual)
        zF=.25/(1+np.exp(-mu));zW=.25/(1+np.exp(mu))
        assert abs(np.mean([int(r['F']) for r in rows])-25*zF/1.25)<.2
        assert abs(np.mean([int(r['W']) for r in rows])-25*zW/1.25)<.2


def test_conditioned_neighbor_proposals_preserve_absolute_pair_clock(tmp_path):
    # V only: a known isolated I/W pair, two immobile B neighbors. Geometry is
    # deliberately selected for calibration, never claimed as unseeded research.
    N=3;case={'id':'find_pair','epsilon':-.7,'df':.3,'eta':.1,'passive_rate':0.,'D_B':0.,'D_I':0.,'D_F':0.,'D_W':0.,'source':'closed','mu':0.,'z_total':1/23,'initial_B_fraction':2/3}
    def adjacent(a,b):
        x=np.array(np.unravel_index(a,(N,)*3,order='F'));y=np.array(np.unravel_index(b,(N,)*3,order='F'))
        return np.minimum(abs(x-y),N-abs(x-y)).sum()==1
    selected=None
    for seed in range(10,2010):
        path=model.run(tmp_path,'geometry-validation',case,n=N,d=3,T=0.,seed=seed,molecules=3)
        cells,pos,states,_=model.fields(path,N,3,0);fuel=np.flatnonzero((cells.ravel(order='F')==4))
        if len(fuel)==1 and np.array_equal(states,[1,1,0]) and all(adjacent(pos[2],p) for p in pos[:2]) and adjacent(pos[2],fuel[0]) and not any(adjacent(p,fuel[0]) for p in pos[:2]):
            selected=seed;break
    assert selected is not None
    case=case|{'id':'isolated_pair'}
    path=model.run(tmp_path,'clock-validation',case,n=N,d=3,T=100000.,seed=selected,molecules=3)
    rows=list(csv.DictReader((path/'series.csv').open()))[500:]
    state=np.array([int(r['B'])-2 for r in rows]);assert set(state)=={0,1}
    probability=1/(1+np.exp(.3-.7*2))
    kIB=.1*np.exp(.7)/6;kBI=.1*np.exp(-.7+.3)/6
    centered=state-state.mean();corr=np.mean(centered[:-1]*centered[1:])/np.mean(centered**2)
    assert abs(state.mean()-probability)<.04
    assert abs(corr-np.exp(-(kIB+kBI)*10))<.06,(corr,kIB,kBI)


def test_sparse_driven_and_closed_ledgers_and_determinism(tmp_path):
    paths=[model.run(tmp_path,'validation',{'id':f'repeat{i}'},n=6,d=3,T=100.,seed=319) for i in range(2)]
    assert (paths[0]/'series.csv').read_bytes()==(paths[1]/'series.csv').read_bytes()
    assert (paths[0]/'state-10-cells.bin').read_bytes()==(paths[1]/'state-10-cells.bin').read_bytes()
    path=model.run(tmp_path,'validation',{'id':'closed','source':'closed'},n=6,d=3,T=100.,seed=319)
    rows=list(csv.DictReader((path/'series.csv').open()))
    assert all(float(r['work'])==0 and int(r['F'])+int(r['W'])==int(rows[0]['F'])+int(rows[0]['W']) for r in rows)
