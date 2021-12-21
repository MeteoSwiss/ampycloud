"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the data module
"""

# Import from Python
import numpy as np
from pytest import raises

# Import from the module to test
from ampycloud.errors import AmpycloudError
from ampycloud.data import CeiloChunk
from ampycloud.utils import mocker
from ampycloud import dynamic, reset_prms

def test_ceilochunk_init():
    """ Test the init method of the CeiloChunk class. """

    n_ceilos = 4
    lookback_time = 1200
    rate = 30

    # Create some fake data to get started
    # 1 very flat layer with no gaps
    mock_data = mocker.mock_layers(n_ceilos,
                                   [{'alt':1000, 'alt_std': 10, 'lookback_time' : lookback_time,
                                     'hit_rate': rate, 'sky_cov_frac': 1,
                                     'period': 100, 'amplitude': 0}])

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)
    # Simple check of the number of ceilometers
    assert len(chunk.data) == len(mock_data)

    # Now initialize a CeiloChunk with the same data, but with the MSA set to 0 ft
    dynamic.AMPYCLOUD_PRMS.MSA = 0
    dynamic.AMPYCLOUD_PRMS.MSA_HIT_BUFFER = 0
    chunk = CeiloChunk(mock_data)
    assert len(chunk.data) == 0
    # Verify the class MSA value is correct too ...
    assert chunk.msa == 0

    # And now again, but this time with a large hit buffer that coverts all the data
    dynamic.AMPYCLOUD_PRMS.MSA = 0
    dynamic.AMPYCLOUD_PRMS.MSA_HIT_BUFFER = mock_data['alt'].max() + 10
    chunk = CeiloChunk(mock_data)
    assert len(chunk.data) == len(mock_data)

    # Let's not forget to reset the dynamic parameters to not mess up the other tests
    reset_prms()

def test_ceilochunk_basic():
    """ Test the basic methods of the CeiloChunk class. """

    n_ceilos = 4
    lookback_time = 1200
    rate = 30

    # Create some fake data to get started
    # 1 very flat layer with no gaps
    mock_data = mocker.mock_layers(n_ceilos,
                                   [{'alt':1000, 'alt_std': 10, 'lookback_time' : lookback_time,
                                     'hit_rate': rate, 'sky_cov_frac': 1,
                                     'period': 100, 'amplitude': 0}])

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)

    # Simple check of the number of ceilometers
    assert len(chunk.ceilos) == n_ceilos
    # Check that I have the correct number of hits per layer
    assert chunk.max_hits_per_layer == np.ceil(lookback_time/rate) * n_ceilos
    # Correct data length
    assert len(chunk.data) == n_ceilos * lookback_time/rate
    # Correct ceilo names
    assert all(item in ['0', '1', '2', '3'] for item in chunk.ceilos)
    # No sli/gro/lay without doing anything
    assert all(item is None for item in [chunk.slices, chunk.groups, chunk.layers])
    # Assess the METAR generation when no processing was done
    with raises(AmpycloudError):
        assert chunk.metar_msg()
    # Idem for the individual sli/gro/lay
    with raises(AmpycloudError):
        assert chunk.metarize('slices')
    # Check that the order is respected
    with raises(AmpycloudError):
        assert chunk.find_groups()
    with raises(AmpycloudError):
        assert chunk.find_layers()

    # Run the slicing step
    chunk.find_slices()
    assert chunk.n_slices == 1

    # Run the grouping step
    chunk.find_groups()
    assert chunk.n_groups == 1

    # Run the layering step
    chunk.find_layers()
    assert chunk.n_layers == 1

    # Make sure that re-generating groups after layers were found raises an issue.
    with raises(AmpycloudError):
        assert chunk.find_groups()

    # Assert the METAR-like message
    assert chunk.metar_msg() == 'OVC009'
    assert chunk.metar_msg(which='groups', synop=True) == 'OVC009'

def test_ceilochunk_nocld():
    """ Test the methods of CeiloChunks when no clouds are seen in the interval. """

    n_ceilos = 4
    lookback_time = 1200
    rate = 30

    # Create some fake data to get started
    # 1 very flat layer with no gaps
    mock_data = mocker.mock_layers(n_ceilos,
                                   [{'alt':1000, 'alt_std': 10, 'lookback_time' : lookback_time,
                                     'hit_rate': rate, 'sky_cov_frac': 0,
                                     'period': 100, 'amplitude': 0}])

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)

    # Do the dance ...
    chunk.find_slices()
    chunk.find_groups()
    chunk.find_layers()

    # Assert the final METAR code is correct
    assert chunk.metar_msg() == 'NCD'

def test_ceilochunk_2lay():
    """ Test the methods of CeiloChunks when 2 layers are seen in the interval. """

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

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)

    # Do the dance ...
    chunk.find_slices()
    chunk.find_groups()
    chunk.find_layers()

    # Assert the final METAR code is correct
    assert chunk.metar_msg() == 'FEW009'
    assert chunk.metar_msg(synop=True) == 'FEW009 FEW019'
