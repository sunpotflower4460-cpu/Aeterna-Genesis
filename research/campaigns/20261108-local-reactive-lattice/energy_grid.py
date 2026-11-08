"""Complete registered energy grid with explicit reuse of identical histories."""
import argparse
import itertools
import json
from pathlib import Path
import experiment as model

HERE=Path(__file__).resolve().parent

def signature(parameters):return tuple(sorted(parameters.items()))

def main(out,seed):
    out=Path(out);reg=json.loads((HERE/'ENERGY_GRID_REGISTRATION.json').read_text())
    existing={}
    for p in sorted((out/'discovery').glob('*/recipe.json')):
        r=json.loads(p.read_text())
        if r['seed']==seed and r['N']==reg['N'] and r['T']==reg['T'] and (p.parent/'summary.json').exists():
            existing[signature(r['parameters'])]=p.parent
    selection={'registration_sha256':model.digest(HERE/'ENERGY_GRID_REGISTRATION.json'),
               'selection_source_sha256':model.digest(__file__),'seed':seed,'slots':[]}
    for mu,df,ts in itertools.product(reg['mu'],reg['df'],reg['ts_fraction']):
        case={'id':f'grid_mu{mu:g}_df{df:g}_ts{ts:g}','mu':mu,'df':df,'ts_fraction':ts}
        reuse=existing.get(signature(model.parameters(case)))
        item={'case':case,'starts_at_zero':True,'reuses_existing_history':bool(reuse)}
        if reuse:item|={'path':str(reuse),'recipe_sha256':model.digest(reuse/'recipe.json'),
                       'summary_sha256':model.digest(reuse/'summary.json')}
        selection['slots'].append(item)
    stage=out/'energy-grid';stage.mkdir(parents=True,exist_ok=True)
    manifest=stage/f'selection-s{seed}.json'
    if manifest.exists():raise FileExistsError(manifest)
    model.save(manifest,selection)
    for item in selection['slots']:
        if item['reuses_existing_history']:continue
        model.run(out,'energy-grid',item['case'],n=reg['N'],d=3,T=reg['T'],seed=seed)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--seed',required=True,type=int);a=p.parse_args();main(a.out,a.seed)
