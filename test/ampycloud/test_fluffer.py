"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the fluffer module
"""

# Import from Python
import warnings
import numpy as np

# Import from this package
from ampycloud.fluffer import get_fluffiness


def test_get_fluffiness():
    """ Test the fluffiness routine """

    # Fluffiness for a single point should be 0
    pts = np.array([[1, 2]])

    # Feeding a single point should not trigger a LOWESS warning
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        out = get_fluffiness(pts)

    assert out[0] == 0
    assert np.array_equal(out[1][:, 1], pts[:, 1])

    # Test the LOWESS warning issued with duplicat points
    pts = np.array([[0, 0], [0, 1], [1, 0]])
    # For some reason, pytest refuses to convert the LOWESS warning into an error ...
    # ... so I need to catch it a bit differently ... sigh !
    with warnings.catch_warnings(record=True) as w_list:
        out = get_fluffiness(pts)

    if len(w_list) > 0:
        print(w_list[0])
    assert len(w_list) == 0
