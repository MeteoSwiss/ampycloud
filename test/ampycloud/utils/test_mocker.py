"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the utils.mocker module
"""

# Import from Python
import numpy as np
import pandas as pd

# Import function to tests
from ampycloud.utils.mocker import mock_layers


def test_mock_layers():
    """ test the mock layer generating routine. """

    # Basic test with 1 ceilo and 1 flat layer
    n_ceilos = 1
    lookback_time = 1200
    hit_rate = 60
    layer_prms =[{'alt':1000, 'alt_std': 100, 'sky_cov_frac': 1,
                  'period': 100, 'amplitude': 0}]
    out = mock_layers(n_ceilos, lookback_time, hit_rate, layer_prms)

    # Correct type ?
    assert isinstance(out, pd.DataFrame)
    assert len(out.columns) == 4
    # Correct number of points ?
    assert len(out) == 1200/60
    # No holes ?
    assert not np.any(out['alt'].isna())
    assert not np.any(out['dt'].isna())
    # Ordered chronologically ?
    assert out['dt'].is_monotonic_increasing

    # Idem, but with holes
    n_ceilos = 2
    lookback_time = 1200
    hit_rate = 60
    layer_prms =[{'alt':1000, 'alt_std': 100, 'sky_cov_frac': 0.5,
                  'period': 100, 'amplitude': 0}]
    out = mock_layers(n_ceilos, lookback_time, hit_rate, layer_prms)

    # Correct number of points ?
    assert len(out) == 1200/60 * n_ceilos
    # Holes present ?
    assert np.any(out['alt'].isna())
    assert not np.any(out['dt'].isna())
    # In good numbers ?
    assert len(out[out['alt'].isna()]) == len(out)/2

    # Now with more than 1 layer
    n_ceilos = 2
    lookback_time = 1200
    hit_rate = 60
    layer_prms =[{'alt':1000, 'alt_std': 100, 'sky_cov_frac': 1,
                  'period': 100, 'amplitude': 0},
                 {'alt':10000, 'alt_std': 200, 'sky_cov_frac': 1,
                  'period': 100, 'amplitude': 0},
                ]
    out = mock_layers(n_ceilos, lookback_time, hit_rate, layer_prms)

    # Correct number of points ?
    assert len(out) == 1200/60 * n_ceilos * len(layer_prms)

    # Now with an incomplete layers, to see if NaN's get handled properly
    n_ceilos = 2
    lookback_time = 1200
    hit_rate = 60
    layer_prms =[{'alt':1000, 'alt_std': 100, 'sky_cov_frac': 1,
                  'period': 100, 'amplitude': 0},
                 {'alt':15000, 'alt_std': 200, 'sky_cov_frac': 1,
                  'period': 100, 'amplitude': 0},
                ]
    out = mock_layers(n_ceilos, lookback_time, hit_rate, layer_prms)

    # Holes present ? There should be None, since we have a second layer complete
    assert np.any(~out['alt'].isna())
    assert not np.any(out['dt'].isna())

    # Make sur I have the correct number of timesteps
    assert len(np.unique(out['dt'])) == n_ceilos * lookback_time/hit_rate
