"""Archive every registered history; verify raw bytes without changing physics.

Run after the registered matrix has finished. Refuses partial/overwritten archives.
Full checkpoints remain in the raw directory; all recipes, summaries and time
series, and an outcome-independent subset of full-precision states, are portable.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
MATRICES = {
    'conserved-mixtures-v01-validated': {
        'discovery': 18, 'verify': 18, 'compare-2d': 18,
        'duration': 3, 'size': 3, 'symmetry': 3, 'dt': 3,
    },
    'reactive-mixture-v01': {'discovery': 1},
    'reactive-mixture-v02': {'discovery': 21, 'verify': 11, 'compare-2d': 21},
    'reactive-mixture-v02-recovery': {'verify': 4},
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def collect(raw, out):
    raw, out = Path(raw), Path(out)
    # Check the complete prospective matrix before creating the archive.
    for campaign, matrix in MATRICES.items():
        counts = collections.Counter(p.parent.parent.name for p in (raw / campaign).rglob('summary.json'))
        if counts != collections.Counter(matrix):
            raise RuntimeError(f'incomplete or unexpected matrix: {campaign}: {dict(counts)} != {matrix}')
        if list((raw / campaign).rglob('FAILURE.json')):
            raise RuntimeError(f'numerical failure requires explicit accounting: {campaign}')
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'qualified_life_vessel_changes': 0, 'expected_matrices': MATRICES,
                'raw_storage': str(raw), 'full_raw_checkpoints_in_git': False,
                'portable_evidence': 'all recipes, summaries and CSV time series; selected states are identified below',
                'runs': [], 'sources': {}, 'three_d_diagnostic_flags': []}
    dimensions = collections.Counter()
    budget = collections.defaultdict(list)
    for campaign in MATRICES:
        for summary in sorted((raw / campaign).rglob('summary.json')):
            directory = summary.parent
            recipe = json.loads((directory / 'recipe.json').read_text())
            result = json.loads(summary.read_text())
            assert result['numerical_budget_pass'] is True
            dimension = recipe['dimension']; dimensions[dimension] += 1
            rows = list(csv.DictReader((directory / 'series.csv').open()))
            assert float(rows[0]['time']) == 0
            duration = recipe.get('duration', recipe.get('T'))
            assert abs(float(rows[-1]['time']) - duration) <= recipe['dt'] + 1e-9
            relative = directory.relative_to(raw)
            record = {'path': str(relative), 'dimension': dimension,
                      'numerical_budget_pass': True, 'qualified_changes': 0, 'files': {}}
            target = out / 'histories' / relative
            target.mkdir(parents=True)
            for name in ['recipe.json', 'summary.json', 'series.csv']:
                shutil.copyfile(directory / name, target / name)
            # Every raw input/checkpoint, including negative controls, is hashed.
            for path in sorted(directory.iterdir()):
                if path.is_file():
                    record['files'][path.name] = {'sha256': sha(path), 'bytes': path.stat().st_size}
            for frame in result['frames']:
                assert record['files'][frame['file']]['sha256'] == frame['sha256']
                authenticity = frame.get('three_d_authenticity')
                if authenticity and not authenticity['genuinely_3d']:
                    manifest['three_d_diagnostic_flags'].append({
                        'run': str(relative), 'frame': frame['file'], 'diagnostic': authenticity,
                        'interpretation': 'retained without gate change; not eligible for a passed-3D-structure claim'})
            if 'energy_drift_max_relative' in result:
                assert result['finite'] is True and result['energy_drift_max_relative'] < .01
                budget['scalar_relative_energy_drift'].append(result['energy_drift_max_relative'])
                budget['scalar_absolute_charge_density_drift'].extend(result['charge_abs_drift'])
            else:
                assert result['atom_drift_max'] < 1e-8 and result['mean_phi_drift_max'] < 1e-8
                energies = [float(r['free_energy']) for r in rows]
                assert max(np.diff(energies)) <= 1e-9
                assert min(float(r['min_concentration']) for r in rows) > 0
                budget['material_absolute_atom_density_drift'].append(result['atom_drift_max'])
                budget['material_absolute_mean_phi_drift'].append(result['mean_phi_drift_max'])
                budget['material_min_concentration'].append(min(float(r['min_concentration']) for r in rows))
            manifest['runs'].append(record)
    manifest['interrupted_histories'] = []
    for campaign in MATRICES:
        for recipe_path in sorted((raw / campaign).rglob('recipe.json')):
            directory = recipe_path.parent
            if (directory / 'summary.json').exists():
                continue
            # Infrastructure interruption is not a success or numerical failure.
            target = out / 'interrupted' / directory.relative_to(raw)
            target.mkdir(parents=True)
            files = {}
            for path in sorted(directory.iterdir()):
                if path.is_file():
                    files[path.name] = {'sha256': sha(path), 'bytes': path.stat().st_size}
                    if path.suffix in ['.json', '.csv']:
                        shutil.copyfile(path, target / path.name)
            manifest['interrupted_histories'].append({'path': str(directory.relative_to(raw)), 'files': files})
    assert len(manifest['interrupted_histories']) == 2
    states = {}; state_records = []
    # All seven discovery cases, same preregistered first seed, regardless of outcome.
    for directory in sorted((raw / 'reactive-mixture-v02' / 'discovery').glob('*-s17')):
        case = directory.name.split('-d')[0]
        for step in [0, 1600]:
            path = directory / f'state-{step}.npz'
            with np.load(path) as fields:
                for field in ['phi', 'concentrations']:
                    key = f'{case}__t{step // 4}__{field}'
                    states[key] = fields[field]
            state_records.append({'source': str(path.relative_to(raw)), 'source_sha256': sha(path),
                                  'prefix': f'{case}__t{step // 4}__'})
    # Finest registered grid, first holdout seed, all three matched cases.
    for case in ['coupled', 'weak_binding', 'frozen_reaction']:
        directory = raw / 'reactive-mixture-v02' / 'verify' / f'{case}-d3-n48-dt0.25-s113'
        if not (directory / 'summary.json').exists():
            directory = raw / 'reactive-mixture-v02-recovery' / 'verify' / directory.name
        path = directory / 'state-1600.npz'
        with np.load(path) as fields:
            for field in ['phi', 'concentrations']:
                states[f'holdout48_{case}__t400__{field}'] = fields[field]
        state_records.append({'source': str(path.relative_to(raw)), 'source_sha256': sha(path),
                              'prefix': f'holdout48_{case}__t400__'})
    np.savez_compressed(out / 'material-states.npz', **states)
    manifest['portable_states'] = {'file': 'material-states.npz', 'sha256': sha(out / 'material-states.npz'),
                                   'selection': 'all cases, fixed first discovery/holdout seeds; no outcome-based selection',
                                   'states': state_records}
    for directory in ['20261108-conserved-mixtures', '20261108-reactive-mixture', '20261108-reactive-mixture-v02']:
        for path in sorted((ROOT / 'research/campaigns' / directory).iterdir()):
            if path.is_file():
                manifest['sources'][str(path.relative_to(ROOT))] = sha(path)
    manifest['dimensions'] = {str(k): v for k, v in sorted(dimensions.items())}
    manifest['total_histories'] = len(manifest['runs'])
    manifest['budgets'] = {key: {'min': min(values), 'max': max(values)} for key, values in budget.items()}
    save(out / 'manifest.json', manifest)
    print(json.dumps({'histories': len(manifest['runs']), 'dimensions': manifest['dimensions'],
                      'qualified_changes': 0, 'budgets': manifest['budgets']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('raw'); parser.add_argument('out')
    args = parser.parse_args()
    collect(args.raw, args.out)
