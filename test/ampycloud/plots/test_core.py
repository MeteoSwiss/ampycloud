"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the plots.core module
"""

from ampycloud import dynamic
from ampycloud.core import demo
from ampycloud.plots.core import raw_data, diagnostic

def test_raw_data(mpls):
    """ Test the raw_data plot."""

    """
    dynamic.MPL_STYLE = 'metsymb'

    # Get some demo chunk data
    _, chunk = demo()

    raw_data(chunk, show_ceilos=True, show=False,
             save_stem='raw_data', save_fmts='pdf',
             ref_name='Test', ref_metar='???')
    """

def test_diagnostic(mpls):
    """ Test the raw_data plot.

    Args:
        mpls: False, or the value of MPL_STYLE requested by the user. This is set automatically
            by a fixture that fetches the corresponding command line argument.
            See conftest.py for details.
    """

    if mpls:
        dynamic.MPL_STYLE = mpls

    # Get some demo chunk data
    _, chunk = demo()

    # Create the diagnsotic plots at the three different upto levels
    diagnostic(chunk, upto='slices', show=False,
               save_stem='pytest_diagnostic_slices', save_fmts='pdf',
               ref_name='Mock data', ref_metar='FEW008 BKN037')

    diagnostic(chunk, upto='groups', show=False,
               save_stem='pytest_diagnostic_groups', save_fmts='pdf',
               ref_name='Mock data', ref_metar='FEW008 BKN037')

    diagnostic(chunk, upto='layers', show=False,
               save_stem='pytest_diagnostic_layers', save_fmts='pdf',
               ref_name='Mock data', ref_metar='FEW008 BKN037')
