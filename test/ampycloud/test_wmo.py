"""
Copyright (c) 2021-2024 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the wmo module
"""

# Import from Python
import numpy as np

# Import from this package
from ampycloud.wmo import perc2okta, height2code


def test_perc2okta():
    """ Test the frac2okta function. """

    assert isinstance(perc2okta(43), np.ndarray)
    assert np.all(perc2okta(2) == np.array([1]))
    assert np.all(perc2okta(np.array([0, 10, 20, 35, 45, 60, 70, 85, 100])) ==
                  np.array([0, 1, 2, 3, 4, 5, 6, 7, 8]))


def test_height2code():
    """ Test the alt2code function, inculding the descaling mode. """

    assert height2code(99.9) == '000'
    assert height2code(100) == '001'
    assert height2code(5555) == '055'
    assert height2code(12345) == '120'
