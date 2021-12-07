"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the BSD-3-Clause license.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the cluster module
"""

# Import from Python
import numpy as np

# Import from the module to test
from ampycloud.cluster import clusterize

def test_clusterize():
    """ Test clusterize(). """

    # Test that None is returned if no algo is specified.
    assert clusterize(np.zeros((10, 2)), algo=None) is None
