"""Registered controls: all trajectories start at zero, immutable outputs."""
import argparse
import json
from pathlib import Path
import experiment as model

HERE=Path(__file__).resolve().parent

def main(out,stage,seeds=None):
    original=json.loads((HERE/'PRE_REGISTRATION.json').read_text())
    reg=json.loads((HERE/'FOLLOWUP_REGISTRATION.json').read_text())
    allcases=original['cases']+reg['new_matched_controls']
    selected=reg['holdouts'] if stage=='holdouts' else reg['volume'] if stage=='volume' else reg['duration'] if stage=='duration' else reg['diagnostic_2d_after_3d']
    cases=allcases if isinstance(selected['cases'],str) else [c for c in allcases if c['id'] in selected['cases']]
    seeds=seeds or selected.get('seeds',[selected.get('seed')])
    stagepath=Path(out)/stage;stagepath.mkdir(parents=True,exist_ok=True)
    # Concurrent independent seed processes write separate selection provenance.
    selection=stagepath/('selection-'+','.join(str(s) for s in seeds)+'.json')
    if selection.exists():raise FileExistsError(selection)
    model.save(selection,{'followup_sha256':model.digest(HERE/'FOLLOWUP_REGISTRATION.json'),
        'selection_source_sha256':model.digest(__file__),'stage':stage,'seeds':seeds,'cases':cases,'starts_at_zero':True})
    for seed in seeds:
        for case in cases:model.run(out,stage,case,n=selected['N'],d=2 if stage=='compare-2d' else 3,T=selected['T'],seed=seed)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['holdouts','volume','duration','compare-2d']);p.add_argument('--out',required=True);p.add_argument('--seeds');a=p.parse_args()
    main(a.out,a.stage,[int(x) for x in a.seeds.split(',')] if a.seeds else None)
