"""Question -> validated input card -> t=0 solver; proposals never manufacture physical outcomes."""
from concurrent.futures import ThreadPoolExecutor

import pytest

from tools.lab.council import Council
from tools.lab.hub import LocalHub
from tools.lab.universe import replay
from tools.lab import council as C


@pytest.fixture
def lab(tmp_path):
    hub = LocalHub()
    uid = hub.create('tdgl-3d', 2)
    hub.run(uid, 2)
    return hub, uid, Council(hub, providers={}, state_dir=tmp_path)


def test_initial_card_changes_start_without_inheriting_interventions(lab):
    hub, uid, c = lab
    original = hub.final_info(uid)
    initial = hub.info(uid)['recipe']['knobs']
    # The parent has advanced and been intervened on. The candidate must still start from its initial recipe.
    law = next(k for k in C.whites.get('tdgl-3d').knobs if k.kind == 'law')
    hub.set_law(uid, {law.name: law.lo})
    before = hub.final_info(uid)
    p = c.add_initial_proposal('core', 'A', {'noise_amplitude': 0.002}, None, 'ゆらぎの違い', '', '')
    assert hub.ids() == [uid]  # proposal creation does not simulate
    assert p['knobs'][law.name] == initial[law.name]
    assert p['base_seed'] == p['seed'] == 2
    result = c.try_proposal(p['id'])
    child = hub.info(result['child'])
    assert child['step'] == 0 and child['recipe']['events'] == []
    assert child['recipe']['knobs']['noise_amplitude'] == 0.002
    assert hub.final_info(uid) == before and before['step'] == original['step']
    hub.run(child['id'], 3)
    final = hub.final_info(child['id'])
    assert replay(final['recipe'], final['step']).sha256() == final['sha256']


@pytest.mark.parametrize('changes,seed', [
    ({'noise_amplitude': float('nan')}, None), ({'noise_amplitude': 99}, None),
    ({'invented_law': 1}, None), ({}, -1), ({}, 1.5), ({}, True), ({}, 10000), ({}, None),
])
def test_invalid_or_unchanged_input_never_creates_a_card_or_worker(lab, changes, seed):
    hub, uid, c = lab
    with pytest.raises((ValueError, KeyError)):
        c.add_initial_proposal('core', uid, changes, seed, '', '', '')
    assert not c.proposals and hub.ids() == [uid]


def test_one_acceptance_per_card_even_with_concurrent_clicks(lab):
    hub, uid, c = lab
    p = c.add_initial_proposal('core', uid, {}, 37, 'seedだけ変える', '', '')
    def accept():
        try:
            return c.try_proposal(p['id'])['child']
        except ValueError:
            return None
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: accept(), range(2)))
    assert len([r for r in results if r]) == 1 and len(hub.ids()) == 2


def test_closed_parent_does_not_destroy_frozen_input(lab):
    hub, uid, c = lab
    p = c.add_initial_proposal('core', uid, {}, 42, '', '', '')
    hub.delete(uid)
    result = c.try_proposal(p['id'])
    assert hub.info(result['child'])['recipe']['seed'] == 42


def test_model_tool_produces_input_and_packet_lists_start_knobs(lab):
    hub, uid, c = lab
    result = c._run_tool('propose_initial', {'parent': 'A', 'changes': [
        {'knob': 'noise_amplitude', 'value': 0.002}], 'seed': None})
    assert '提案カード' in result and len(hub.ids()) == 1
    packet = C.observe.build(hub, [uid], motion_frames=0)
    assert 'noise_amplitude' in packet['text'] and 'propose_initial' in packet['text']


def test_observation_failure_does_not_leave_ai_stuck_busy(lab, monkeypatch):
    hub, uid, c = lab
    def fail(*args, **kwargs):
        raise ValueError('observation failed')
    monkeypatch.setattr(C.observe, 'build', fail)
    with pytest.raises(ValueError):
        c.look([uid])
    assert not c.busy
