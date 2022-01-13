"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the icao module
"""

# Import from this package
from ampycloud.icao import significant_cloud

def test_significant_cloud():
    """ Test the significant_cloud function. """

    assert isinstance(significant_cloud([0]), list)
    assert significant_cloud([6, 6, 6]) == [True, True, True]
    # The following tests may need to be adjusted depending on #47
    assert significant_cloud([6, 6, 6, 6, 6]) == [True, True, True, True, True]
    assert significant_cloud([6, 1, 1, 6, 6]) == [True, False, False, True, True]
    assert significant_cloud([6, 1, 3, 6, 6]) == [True, False, True, True, True]
    assert significant_cloud([6, 5, 3]) == [True, True, False]
