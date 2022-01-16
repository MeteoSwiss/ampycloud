"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the core module
"""


#Import from Python
import os
from pathlib import Path
import numpy as np
import pandas as pd

# Import from ampycloud
from ampycloud import dynamic, reset_prms
from ampycloud.utils import mocker
from ampycloud.data import CeiloChunk
from ampycloud.core import copy_prm_file, reset_prms, run, metar, demo

def test_copy_prm_file():
    """ Test the copy_prm_file routine."""

    # Create a temporary directory
    save_loc = Path('./tmp_pytest/')
    if not save_loc.exists():
        save_loc.mkdir()

    # Run the routine
    copy_prm_file(save_loc=save_loc, which='default')

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
    assert out.metar_msg() == 'FEW009'

    # While I'm at it, also check the metar routines, that are so close
    assert metar(mock_data) == 'FEW009'

def test_run_single_point():
    """ Test the code when a single data point is fed to it. """

    # Set no lower limits to compute oktas
    dynamic.OKTA_LIM0 = 0

    # Let's create some data with a single valid point
    data = pd.DataFrame([['1', -100, 2000, 1], ['1', -99, np.nan, 1]],
                        columns=['ceilo', 'dt', 'alt', 'type'])
    data['ceilo'] = data['ceilo'].astype(str)
    data['dt'] = data['dt'].astype(float)
    data['alt'] = data['alt'].astype(float)
    data['type'] = data['type'].astype(int)

    # Run the code
    out = run(data)
    assert out.metar_msg() == 'SCT020'

    # Do it with a single point
    data.drop(1, inplace=True)
    # Run the code
    out = run(data)
    assert out.metar_msg() == 'OVC020'

    # Reset the parameters
    reset_prms()

def test_demo():
    """ test the demo routine. """

    mock_data, chunk = demo()

    assert isinstance(chunk, CeiloChunk)
    assert isinstance(mock_data, pd.DataFrame)
