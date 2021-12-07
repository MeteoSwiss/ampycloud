"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the BSD-3-Clause license.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the layer module
"""

# Import from Python
import numpy as np

# Import from the module to test
from ampycloud.layer import ncomp_from_gmm, best_gmm, scores2nrl

# Define a proper random number generator
np.random.seed(42)

def test_scores2nrl():
    """ Test the scores2nrl() function. """

    # Basic check to make sure I return the correct shape and values ...
    assert len(scores2nrl(np.ones(3))) == 3
    assert len(np.unique(scores2nrl(np.ones(3)))) == 1
    assert np.unique(scores2nrl(np.ones(4))) == 1/4

def test_best_gmm():
    """ Test the best_gmm() function """

    # Choose the smallest scores when asked to do so
    assert best_gmm(np.array([3, 1, 2]), mode='delta', min_prob=1., delta_mul_gain= 1.) == 1
    assert best_gmm(np.array([3, 1, 2]), mode='prob', min_prob=1., delta_mul_gain= 1.) == 1

    # Correctly handle delta_mul_gain
    assert best_gmm(np.array([3, 2, 1.9]), mode='delta', min_prob=1., delta_mul_gain=0.75) == 1
    # Correctly handle min_prob
    assert best_gmm(np.array([3, 2, 1]), mode='prob', min_prob=0.1, delta_mul_gain=1) == 0
    assert best_gmm(np.array([3, 2, 1]), mode='prob', min_prob=0.2, delta_mul_gain=1) == 1
    assert best_gmm(np.array([3, 2, 1]), mode='prob', min_prob=0.4, delta_mul_gain=1) == 2


def test_ncomp_from_gmm():
    """ Tests ncomp_from_gmm, in particular the ability to detect multiple components in
    clear-cut cases. """

    # Generate random data with a normal distribution, and offset by 5-sigma each.
    # This is a level at which I should always be able to find the correct number of components.
    comp1 = np.random.randn(100)
    comp2 = np.random.randn(100) + 5
    comp3 = np.random.randn(100) + 10

    out, _, _ = ncomp_from_gmm(comp1,
                               scores='BIC', rescale_0to=100,
                               delta_mul_gain=0.95, mode='delta')
    assert out == 1

    out, _, _ = ncomp_from_gmm(np.concatenate([comp1, comp2]),
                               scores='BIC', rescale_0to=100,
                               delta_mul_gain=0.95, mode='delta')
    assert out == 2

    out, _, _ = ncomp_from_gmm(np.concatenate([comp1, comp2, comp3]),
                               scores='BIC', rescale_0to=100,
                               delta_mul_gain=0.95, mode='delta')
    assert out == 3

    # Check that I can "force" 1 component in all cases ...
    out, _, _ = ncomp_from_gmm(np.concatenate([comp1, comp2, comp3]),
                               scores='BIC', rescale_0to=100,
                               delta_mul_gain=0., mode='delta')
    assert out == 1