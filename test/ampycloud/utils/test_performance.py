"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the utils.performance module
"""

# Import from ampycloud
from ampycloud.utils.performance import get_speed_benchmark


def test_speed_benchmark():
    """ This routine tests the get_speed_benchmark function. """

    # Run the fct, and check the output. This is not actually meant to check the speed of the code.
    out = get_speed_benchmark(niter=2)

    assert isinstance(out, tuple)
