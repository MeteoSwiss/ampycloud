"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the plots.utils module
"""

# Import from ampycloud
from ampycloud.plots.tools import valid_styles


def test_valid_styles():
    """ Test the valid_styles routine. """

    assert all(item in valid_styles() for item in ['base', 'latex', 'metsymb'])
