"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the plots.core module
"""

# Import from Python
from pathlib import Path
import numpy as np
import pandas as pd

from ampycloud import dynamic, reset_prms, run
from ampycloud.core import demo
from ampycloud.plots.core import diagnostic

def test_diagnostic(mpls):
    """ Test the raw_data plot.

    Args:
        mpls: False, or the value of MPL_STYLE requested by the user. This is set automatically
            by a fixture that fetches the corresponding command line argument.
            See conftest.py for details.
    """

    reset_prms()

    if mpls:
        dynamic.AMPYCLOUD_PRMS.MPL_STYLE = mpls

    # Set some MSA to see it on the plot
    dynamic.AMPYCLOUD_PRMS.MSA = 12345

    # Get some demo chunk data
    _, chunk = demo()

    base_name = 'pytest_diagnostic_'
    sufxs = ['raw_data', 'slices', 'groups', 'layers']

    # Create the diagnsotic plots at the four different upto levels
    for sufx in sufxs:
        diagnostic(chunk, upto=sufx, show_ceilos=True, show=False,
                   save_stem=base_name+sufx, save_fmts='png',
                   ref_metar_origin='Mock data', ref_metar='FEW009 SCT018 BKN038')

        assert Path(base_name+sufx+'.pdf').exists

    # Reset the dynamic params to their default to not mess up the other tests
    reset_prms()


def test_empty_plot(mpls):
    """ Test that all goes well, when I just get NaNs.

    Args:
        mpls: False, or the value of MPL_STYLE requested by the user. This is set automatically
            by a fixture that fetches the corresponding command line argument.
            See conftest.py for details.

    """

    if mpls:
        dynamic.AMPYCLOUD_PRMS.MPL_STYLE = mpls

    # Let's create some data with only NaNs
    data = pd.DataFrame([['1', -100, np.nan, 0], ['1', -99, np.nan, 0]],
                        columns=['ceilo', 'dt', 'alt', 'type'])
    data['ceilo'] = data['ceilo'].astype(pd.StringDtype())
    data['dt'] = data['dt'].astype(float)
    data['alt'] = data['alt'].astype(float)
    data['type'] = data['type'].astype(int)

    # Run ampycloud
    chunk = run(data)

    # Uncomment the line below once pytst 7.0 can be pip-installed
    #with pytest.does_not_warn():
    if True:
        diagnostic(chunk, upto='layers', show_ceilos=False, show=False,
                   save_stem='pytest_empty_plot', save_fmts='png',
                   ref_metar_origin='Empty data', ref_metar='NCD')

    assert Path('pytest_empty_plot.pdf').exists
