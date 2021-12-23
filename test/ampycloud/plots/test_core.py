"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the plots.core module
"""

# Import from Python
from pathlib import Path

from ampycloud import dynamic, reset_prms
from ampycloud.core import demo
from ampycloud.plots.core import diagnostic

def test_diagnostic(mpls):
    """ Test the raw_data plot.

    Args:
        mpls: False, or the value of MPL_STYLE requested by the user. This is set automatically
            by a fixture that fetches the corresponding command line argument.
            See conftest.py for details.
    """

    if mpls:
        dynamic.AMPYCLOUD_PRMS.MPL_STYLE = mpls

    dynamic.AMPYCLOUD_PRMS.MSA=12345

    # Get some demo chunk data
    _, chunk = demo()

    base_name = 'pytest_diagnostic_'
    sufxs = ['raw_data', 'slices', 'groups', 'layers']

    # Create the diagnsotic plots at the four different upto levels
    for sufx in sufxs:
        diagnostic(chunk, upto=sufx, show_ceilos=True, show=False,
                   save_stem=base_name+sufx, save_fmts='pdf',
                   ref_metar_origin='Mock data', ref_metar='FEW008 BKN037')

        assert Path(base_name+sufx+'.pdf').exists

    # Reset the dynamic params to their default to not mess up the other tests
    reset_prms()
