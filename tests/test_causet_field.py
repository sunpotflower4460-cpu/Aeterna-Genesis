"""Light-cone-first white (P7-5 prototype): a field on a causal set, checked against the continuum."""
import numpy as np

from genesis.models import causet_field as cf


def test_hop_and_stop_on_a_hand_made_order():
    # a chain 0 ≺ 1 ≺ 2 and an element 3 that only 0 precedes
    R = np.zeros((4, 4), bool)
    R[0, 1] = R[1, 2] = R[0, 2] = R[0, 3] = True
    rho, m = 10.0, 2.0
    a = m * m / rho
    K = cf.retarded_from(R, rho, m, 0)
    assert np.allclose(K, [0.0, 0.5, 0.5 - 0.25 * a, 0.5])      # one chain with one hop reaches 2
    assert np.allclose(cf.retarded_matrix(R, rho, m)[0], K)
    past, n = cf.between_counts(R, 2)
    assert past.tolist() == [0, 1] and n.tolist() == [1, 0]


def test_element_rule_equals_the_matrix_and_is_zero_outside_the_cone():
    pts, R = cf.diamond_with_tips(300, seed=4)
    K = cf.retarded_from(R, 600.0, 5.0, 0)
    assert np.allclose(K, cf.retarded_matrix(R, 600.0, 5.0)[0], atol=1e-12)
    j = 150
    Kj = cf.retarded_from(R, 600.0, 5.0, j)
    assert np.all(Kj[~R[j]] == 0.0)                              # nothing arrives outside the future of j
    assert np.array_equal(cf.diamond_with_tips(300, seed=4)[1], R)  # deterministic


def _bin_error(N, seed, m=5.0):
    pts, R = cf.diamond_with_tips(N, seed)
    K = cf.retarded_from(R, 2.0 * N, m, 0)
    tau = cf.proper_time(pts, 0)
    idx = np.minimum((tau * 10).astype(int), 9)
    inside = R[0]
    return max(abs(K[inside & (idx == b)].mean() - cf.continuum_retarded(tau[inside & (idx == b)], m).mean())
               for b in range(10))


def test_chains_grow_the_bessel_propagator_and_converge():
    """Mean of K over proper-time bins vs ½ J0(mτ) (m = 5: two sign changes inside the diamond)."""
    small = [_bin_error(500, s) for s in range(3)]
    large = [_bin_error(2000, s) for s in range(3)]
    assert max(large) < 0.03
    assert np.mean(large) < 0.6 * np.mean(small)


def test_smeared_box_is_right_on_average_but_noisy():
    """Mean over sprinklings of B_ε φ at the top tip: φ = (t−1)² → −2, φ = x² → +2 (□ = −∂t² + ∂x²).
    A single sprinkling scatters by more than the signal (the known fluctuation problem)."""
    vals = []
    for s in range(20):
        pts, R = cf.diamond_with_tips(2000, seed=100 + s)
        x = len(pts) - 1
        vals.append([cf.smeared_box(R, 4000.0, 0.03, (pts[:, 0] - 1) ** 2, x),
                     cf.smeared_box(R, 4000.0, 0.03, pts[:, 1] ** 2, x)])
    v = np.array(vals)
    mean, sem = v.mean(0), v.std(0) / np.sqrt(len(v))
    assert abs(mean[0] + 2) < 3 * sem[0] + 0.5 and abs(mean[1] - 2) < 3 * sem[1] + 0.5
    assert mean[0] < 0 < mean[1]
    assert v.std(0).min() > 2.0
