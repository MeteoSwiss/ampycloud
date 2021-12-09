"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the plots.core module
"""

from ampycloud import dynamic
from ampycloud.core import demo
from ampycloud.plots.core import raw_data, layers

def test_raw_data():
    """ Test the raw_data plot."""

    """
    dynamic.MPL_STYLE = 'metsymb'

    # Get some demo chunk data
    _, chunk = demo()

    raw_data(chunk, show_ceilos=True, show=False,
             save_stem='raw_data', save_fmts='pdf',
             ref_name='Test', ref_metar='???')
    """

def test_layers():
    """ Test the raw_data plot."""

    dynamic.MPL_STYLE = 'metsymb'

    # Get some demo chunk data
    _, chunk = demo()

    layers(chunk, show=False,
           save_stem='layers', save_fmts='pdf',
           ref_name='Test', ref_metar='???')
