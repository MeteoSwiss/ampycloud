"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the core module
"""


#Import from Python
import os
from pathlib import Path
import pandas as pd

# Import from ampycloud
from ampycloud import dynamic
from ampycloud.utils import mocker
from ampycloud.data import CeiloChunk
from ampycloud.core import copy_prm_file, reset_prms, run, synop, metar, demo


def test_copy_prm_file():
    """ Test the copy_prm_file routine."""

    # Create a temporary directory
    save_loc = Path('./tmp_pytest/')
    if not save_loc.exists():
        save_loc.mkdir()

    # Run the routine
    copy_prm_file(save_loc=save_loc, which='defaults')

    # Clean things up if all went fine
    _ = [os.remove(item) for item in save_loc.glob('*')]
    save_loc.rmdir()

def test_reset_prms():
    """ Test the reset_prms routine. """

    # First, let's change one of the dynamic parameter
    ref_val = dynamic.AMPYCLOUD_PRMS.OKTA_LIM0
    dynamic.AMPYCLOUD_PRMS.OKTA_LIM0 = -1
    assert dynamic.AMPYCLOUD_PRMS.OKTA_LIM0 == -1
    assert dynamic.AMPYCLOUD_PRMS.SLICING_PRMS.dt_scale_mode == 'const'

    # Then try to reset it
    reset_prms()

    assert dynamic.AMPYCLOUD_PRMS.OKTA_LIM0 == ref_val

def test_run():
    """ Test the run routine. """

    # Let's create some mock data
    n_ceilos = 4
    lookback_time = 1200
    rate = 30

    # Create some fake data to get started
    # 1 very flat layer with no gaps
    mock_data = mocker.mock_layers(n_ceilos,
                                   [{'alt':1000, 'alt_std': 10, 'lookback_time' : lookback_time,
                                     'hit_rate': rate, 'sky_cov_frac': 0.5,
                                     'period': 100, 'amplitude': 0},
                                    {'alt':2000, 'alt_std': 10, 'lookback_time' : lookback_time,
                                       'hit_rate': rate, 'sky_cov_frac': 0.5,
                                       'period': 100, 'amplitude': 0}])

    out = run(mock_data)

    assert isinstance(out, CeiloChunk)
    assert out.metar_msg(synop=True) == 'FEW009 FEW019'
    assert out.metar_msg(synop=False) == 'FEW009'

    # While I'm at it, also check the metar and synop routines, that are so close

    assert synop(mock_data) == 'FEW009 FEW019'
    assert metar(mock_data) == 'FEW009'

def test_demo():
    """ test the demo routine. """

    mock_data, chunk = demo()

    assert isinstance(chunk, CeiloChunk)
    assert isinstance(mock_data, pd.DataFrame)
