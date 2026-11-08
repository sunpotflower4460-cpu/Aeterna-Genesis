"""Complete registered encounter grid, exact-law reuse, no outcome selection."""
import argparse
import itertools
import json
from pathlib import Path
import experiment_sparse as model

HERE=Path(__file__).resolve().parent

def signature(parameters):return tuple(sorted(parameters.items()))

def main(out,seed):
    out=Path(out);reg=json.loads((HERE/'ENCOUNTER_GRID_REGISTRATION.json').read_text());g=reg['grid'];existing={}
    for p in sorted((out/'discovery').glob('*/recipe.json')):
        r=json.loads(p.read_text())
        if r['seed']==seed and r['N']==reg['N'] and r['T']==reg['T'] and (p.parent/'summary.json').exists():existing[signature(r['parameters'])]=p.parent
    selection={'registration_sha256':model.digest(HERE/'ENCOUNTER_GRID_REGISTRATION.json'),'selection_source_sha256':model.digest(__file__),'seed':seed,'slots':[]}
    for eta,D,source,df in itertools.product(g['eta'],g['D_F_and_D_W'],g['source'],g['df']):
        case={'id':f'enc_eta{eta:g}_D{D:g}_{source}_df{df:g}','eta':eta,'D_F':D,'D_W':D,'source':source,'df':df,'mu':g['mu']}
        reuse=existing.get(signature(model.parameters(case)));item={'case':case,'reuses_existing_history':bool(reuse)}
        if reuse:item|={'path':str(reuse),'recipe_sha256':model.digest(reuse/'recipe.json'),'summary_sha256':model.digest(reuse/'summary.json')}
        selection['slots'].append(item)
    assert len(selection['slots'])==24 and sum(x['reuses_existing_history'] for x in selection['slots'])==5
    stage=out/'encounter-grid';stage.mkdir(parents=True,exist_ok=True);path=stage/f'selection-s{seed}.json'
    if path.exists():raise FileExistsError(path)
    model.save(path,selection)
    for item in selection['slots']:
        if not item['reuses_existing_history']:model.run(out,'encounter-grid',item['case'],n=reg['N'],d=3,T=reg['T'],seed=seed)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--seed',type=int,required=True);a=p.parse_args();main(a.out,a.seed)
