"""Instrument checks; these are validation, never research discoveries."""
import os
import numpy as np
import pytest
import run as campaign

def test_initial_state_is_one_continuum_realization_across_resolutions():
    coarse=campaign.initial(24,3,11)
    fine=campaign.initial(48,3,11)
    assert np.max(np.abs(fine[:,::2,::2,::2]-coarse))<2e-15

def test_no_initial_dense_object_and_common_rotation_across_couplings():
    u=campaign.initial(48,3,11)
    for i in [0,2]:
        den=u[i]**2+u[i+1]**2
        assert not (den>1.5*den.mean()).any()
    assert np.ptp(u[5])==0
    assert np.array_equal(u[5],-u[7])

def test_exact_species_symmetry_is_preserved(tmp_path):
    u=campaign.initial(16,3,11)
    u[2]=u[0];u[3]=-u[1];u[6]=u[4];u[7]=-u[5]
    out=tmp_path/'symmetry'
    campaign.execute(u,out,64.,.15,3.,.01)
    v=np.fromfile(out/'state-20.bin').reshape(u.shape)
    assert np.array_equal(v[0],v[2])
    assert np.array_equal(v[1],-v[3])
    assert np.array_equal(v[4],v[6])
    assert np.array_equal(v[5],-v[7])

def test_parallel_stencil_preserves_deterministic_state(tmp_path,monkeypatch):
    u=campaign.initial(48,3,11)
    values=[]
    for threads in [1,3]:
        monkeypatch.setenv('OMP_NUM_THREADS',str(threads))
        out=tmp_path/f'threads-{threads}'
        campaign.execute(u,out,64.,.15,3.,-.01)
        values.append((out/'state-20.bin').read_bytes())
    assert values[0]==values[1]

def test_output_refuses_existing_directory(tmp_path):
    with pytest.raises(FileExistsError):
        campaign.execute(campaign.initial(8,3,11),tmp_path,64.,.15,3.,0.)
