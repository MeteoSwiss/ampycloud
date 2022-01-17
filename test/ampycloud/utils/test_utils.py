"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the utils.performance module
"""

# Import form Python
import numpy as np

# Import from ampycloud
from ampycloud.utils.utils import tmp_seed

def test_tmp_seed():
    """ This routine tests the tmp_seed. """

    # Let's set a seed, get some random numbers, then check if I can reproduce this with tmp_seed.
    np.random.seed(42)
    a = np.random.random(100)
    b = np.random.random(10)
    c = np.random.random(1)

    # Make sure I get the concept of random numbers ...
    np.random.seed(43)
    a43 = np.random.random(100)
    assert np.all(a != a43)

    np.random.seed(42)
    a42 = np.random.random(100)
    assert np.all(a == a42)

    # Now, actually check the function I am interested in.
    np.random.seed(43) # Set a seed
    with tmp_seed(42): # Temporarily set anopther one
        assert np.all(a == np.random.random(100))
        assert np.all(b == np.random.random(10))
        assert np.all(c == np.random.random(1))

    # Can I recover the original seed ?
    assert np.all(a43 == np.random.random(100))
