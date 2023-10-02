"""
Copyright (c) 2021-2023 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the plots.utils module
"""

# Import from Python
import matplotlib as mpl

# Import from ampycloud
from ampycloud import dynamic
from ampycloud.plots.tools import valid_styles, set_mplstyle


def test_valid_styles():
    """ Test the valid_styles routine. """

    assert all(item in valid_styles() for item in ['base', 'latex', 'metsymb'])


def test_issue18():
    """ Verify that custom styles can be set within a specific context ... and stay there ..."""

    @set_mplstyle
    def check_plot_context():
        """ Extract the value of some key rcParams """

        return (mpl.rcParams['text.usetex'], mpl.rcParams['text.latex.preamble'])

    # By default, we are not using the system-wide LaTeX engine.
    dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] = 'base'
    assert not check_plot_context()[0]

    # Now, change the style and check again
    dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] = 'metsymb'
    assert check_plot_context()[0]
    assert 'metsymb' in check_plot_context()[1]

    # Check that the out-of-context parameters were untouched
    assert not mpl.rcParams['text.usetex']
    assert mpl.rcParams['text.latex.preamble'] == ''

    # Finally, let's check that I can also alter the preamble in context
    dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] = 'latex'
    assert 'metsymb' not in check_plot_context()[1]
