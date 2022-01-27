"""
Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the plots.secondary module
"""

# Import from Python
from pathlib import Path

from ampycloud import dynamic
from ampycloud.plots.secondary import scaling_fcts


def test_scaling_fcts(mpls):
    """ Test the scaling_fcts plot.

    Args:
        mpls: False, or the value of MPL_STYLE requested by the user. This is set automatically
            by a fixture that fetches the corresponding command line argument.
            See conftest.py for details.

    """

    if mpls:
        dynamic.AMPYCLOUD_PRMS.MPL_STYLE = mpls

    scaling_fcts(show=False, save_stem='pytest_scaling_fcts', save_fmts=['png'])
    assert Path('pytest_large_dts.pdf').exists
