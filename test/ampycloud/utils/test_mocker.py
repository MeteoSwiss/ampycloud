"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the mocker module
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
    layer_prms =[{'alt':1000, 'alt_std': 100, 'lookback_time' : 1200,
                  'hit_rate': 60, 'sky_cov_frac': 1,
                  'period': 100, 'amplitude': 0}]
    out = mock_layers(n_ceilos, layer_prms)

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
    layer_prms =[{'alt':1000, 'alt_std': 100, 'lookback_time' : 1200,
                  'hit_rate': 60, 'sky_cov_frac': 0.5,
                  'period': 100, 'amplitude': 0}]
    out = mock_layers(n_ceilos, layer_prms)

    # Correct number of points ?
    assert len(out) == 1200/60 * n_ceilos
    # Holes present ?
    assert np.any(out['alt'].isna())
    assert not np.any(out['dt'].isna())
    # In good numbers ?
    assert len(out[out['alt'].isna()]) == len(out)/2

    # And finally with more than 1 layer
    n_ceilos = 2
    layer_prms =[{'alt':1000, 'alt_std': 100, 'lookback_time' : 1200,
                  'hit_rate': 60, 'sky_cov_frac': 0.5,
                  'period': 100, 'amplitude': 0},
                 {'alt':2000, 'alt_std': 200, 'lookback_time' : 600,
                  'hit_rate': 60, 'sky_cov_frac': 1,
                  'period': 100, 'amplitude': 0},
                ]
    out = mock_layers(n_ceilos, layer_prms)
    # Correct number of points ?
    assert len(out) == 1200/60 * n_ceilos + 600/60 * n_ceilos
    # Holes present ?
    assert np.any(out['alt'].isna())
    assert not np.any(out['dt'].isna())
