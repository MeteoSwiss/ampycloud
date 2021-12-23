"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

File contains: a very simple script that can generate the demo diagnostic plot for the docs
"""

# Import what I need
from pathlib import Path
import ampycloud
from ampycloud import dynamic
import ampycloud.plots as ampyplots


# Adjust the ampycloud scientific parameters
dynamic.AMPYCLOUD_PRMS.MSA = 10000

# Generate and process the mock data
mock_data, chunk = ampycloud.demo()

# Plot it
ampyplots.diagnostic(chunk, upto='layers', show=False, save_fmts=['png'], ref_metar='FEW008 BKN037',
                     ref_metar_origin='Mock data',
                     save_stem=Path(__file__).parent / 'ampycloud_canonical_mock_demo')
