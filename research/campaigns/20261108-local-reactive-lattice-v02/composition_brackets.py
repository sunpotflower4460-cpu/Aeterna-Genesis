"""Prospective matched-composition nulls, all from t=0, no new physics code."""
import argparse
import itertools
import json
from pathlib import Path
import experiment as model

HERE=Path(__file__).resolve().parent

def main(out,seed):
    reg=json.loads((HERE/'COMPOSITION_BRACKET_REGISTRATION.json').read_text());c=reg['conditions']
    cases=[{'id':f'frozen_B{f:g}_DI{D:g}','rate':0.,'mu':0.,'df':1.2,'D':100.,'D_I':D,'initial_B_fraction':f}
           for f,D in itertools.product(c['initial_B_fraction'],c['D_I'])]
    directory=Path(out)/'composition-brackets';directory.mkdir(parents=True,exist_ok=True)
    selection=directory/f'selection-s{seed}.json'
    if selection.exists():raise FileExistsError(selection)
    model.save(selection,{'registration_sha256':model.digest(HERE/'COMPOSITION_BRACKET_REGISTRATION.json'),
        'selection_source_sha256':model.digest(__file__),'cases':cases,'seed':seed,'starts_at_zero':True,'scheduler':1})
    for case in cases:model.run(out,'composition-brackets',case,n=c['N'],d=c['dimension'],T=c['T'],seed=seed,scheduler=1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--seed',required=True,type=int);a=p.parse_args();main(a.out,a.seed)
