"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the data module
"""

# Import from Python
import warnings
import numpy as np
import pandas as pd
from pytest import raises, warns, mark, param

# Import from the module to test
from ampycloud.errors import AmpycloudError, AmpycloudWarning
from ampycloud.data import CeiloChunk
from ampycloud.utils import mocker
from ampycloud import dynamic, reset_prms, hardcoded


def test_ceilochunk_init():
    """ Test the init method of the CeiloChunk class. """

    n_ceilos = 4
    lookback_time = 1200
    rate = 30

    # Create some fake data to get started
    # 1 very flat layer with no gaps
    mock_data = mocker.mock_layers(n_ceilos, lookback_time, rate,
                                   [{'alt': 1000, 'alt_std': 10, 'sky_cov_frac': 1,
                                     'period': 100, 'amplitude': 0}])
    # The following line is required as long as the mocker module issues mock data with type 99.
    mock_data.iloc[-1, mock_data.columns.get_loc('type')] = 1

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)
    # Simple check of the number of ceilometers
    assert len(chunk.data) == len(mock_data)

    # Now initialize a CeiloChunk with the same data, but with the MSA set to 0 ft
    dynamic.AMPYCLOUD_PRMS['MSA'] = 0
    dynamic.AMPYCLOUD_PRMS['MSA_HIT_BUFFER'] = 0
    chunk = CeiloChunk(mock_data)
    # Applying the MSA should crop any Type 2 or more hits, and change Type 1 or less to Type 0.
    assert len(chunk.data) == len(mock_data[mock_data.type <= 1])
    assert not np.any(chunk.data.type > 0)
    # Verify the class MSA value is correct too ...
    assert chunk.msa == 0

    # And now again, but this time with a large hit buffer that coverts all the data
    dynamic.AMPYCLOUD_PRMS['MSA'] = 0
    dynamic.AMPYCLOUD_PRMS['MSA_HIT_BUFFER'] = mock_data['alt'].max() + 10
    chunk = CeiloChunk(mock_data)
    assert len(chunk.data) == len(mock_data)

    # Check that feeding an empty dataframe crashes properly
    with raises(AmpycloudError):
        _ = CeiloChunk(mock_data[:0])

    # Check the ability to manually specifiy parameters at init without messing up the default ones
    chunk = CeiloChunk(mock_data, prms={'MSA': -30})
    assert chunk.msa == -30
    assert dynamic.AMPYCLOUD_PRMS['MSA'] == 0

    # Check the ability to set nested parameters in one go
    chunk = CeiloChunk(mock_data, prms={'GROUPING_PRMS': {'alt_pad_perc': 'test'}})
    assert chunk.prms['GROUPING_PRMS']['alt_pad_perc'] == 'test'
    assert dynamic.AMPYCLOUD_PRMS['GROUPING_PRMS']['alt_pad_perc'] == +10

    # Check that warnings are raised in case bad parameters are given
    with warns(AmpycloudWarning):
        chunk = CeiloChunk(mock_data, prms={'SMTH_BAD': 0})
        assert chunk.prms == dynamic.AMPYCLOUD_PRMS

    # Let's not forget to reset the dynamic parameters to not mess up the other tests
    reset_prms()


def test_ceilochunk_basic():
    """ Test the basic methods of the CeiloChunk class. """

    n_ceilos = 4
    lookback_time = 1200
    rate = 30

    # Create some fake data to get started
    # 1 very flat layer with no gaps
    mock_data = mocker.mock_layers(n_ceilos, lookback_time, rate,
                                   [{'alt': 1000, 'alt_std': 10, 'sky_cov_frac': 1,
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
    assert chunk.metar_msg(which='groups') == 'OVC009'


@mark.parametrize('altitude1,altitude2,altitude3,ngroups_expected', [
    param(250., 800., 1200., 3, id='gt min sep'),
    param(250., 500., 1200., 3, id='eq min sep'),
    param(250., 350., 1200., 2, id='gt min sep'),
    param(250., 350., 500., 2, id='multiple overlaps no second merge'),
    param(250., 350., 400., 1, id='multiple overlaps with second merge'),
])
def test_group_separation(
    altitude1: float, altitude2: float, altitude3: float, ngroups_expected: int
):
    """Test if the separation of close groups works as intended."""

    #create some fake data:
    fake_hits = [altitude1] * 50 + [altitude2] * 50 + [altitude3] * 50
    fake_data = pd.DataFrame({
        'ceilo': ['Ceilometer.PO'] * 150,
        'dt': [t for t in range(-1500, 0, 10)],
        'alt': fake_hits,
        'type': [1] * 150,
    })
    fake_grp_ids = [1] * 50 + [2] * 50 + [3] * 50
    fake_data['ceilo'] = fake_data['ceilo'].astype(pd.StringDtype())
    fake_data['dt'] = fake_data['dt'].astype(np.float64)
    ceilo_chunk = CeiloChunk(
        fake_data,
        prms={'MIN_SEP_VALS': [250, 1000], 'MIN_SEP_LIMS': [10000]}
    )
    ceilo_chunk.data['group_id'] = fake_grp_ids
    ceilo_chunk._merge_close_groups()

    assert len(ceilo_chunk.data['group_id'].unique()) == ngroups_expected

    reset_prms()

def test_bad_layer_sep_lims():
    """ Test that giving problematic layer separation limits does raise an error. """

    # Make sure that bad layering min sep values raises an error
    dynamic.AMPYCLOUD_PRMS['MIN_SEP_VALS'] = [150, 1000]
    dynamic.AMPYCLOUD_PRMS['MIN_SEP_LIMS'] = [5000, 10000]

    n_ceilos = 4
    lookback_time = 1200
    rate = 30

    # Create some fake data to get started
    # 1 very flat layer with no gaps
    mock_data = mocker.mock_layers(n_ceilos, lookback_time, rate,
                                   [{'alt': 1000, 'alt_std': 10, 'sky_cov_frac': 1,
                                     'period': 100, 'amplitude': 0}])

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)

    # Do the dance ...
    chunk.find_slices()

    with raises(AmpycloudError):
        chunk.find_groups()
        chunk.find_layers()

    reset_prms()


def test_ceilochunk_nocld():
    """ Test the methods of CeiloChunks when no clouds are seen in the interval. """

    n_ceilos = 4
    lookback_time = 1200
    rate = 30

    # Create some fake data to get started
    # 1 very flat layer with no gaps
    mock_data = mocker.mock_layers(n_ceilos, lookback_time, rate,
                                   [{'alt': 1000, 'alt_std': 10, 'sky_cov_frac': 0,
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
    mock_data = mocker.mock_layers(n_ceilos, lookback_time, rate,
                                   [{'alt': 1000, 'alt_std': 10, 'sky_cov_frac': 0.5,
                                     'period': 100, 'amplitude': 0},
                                    {'alt': 2000, 'alt_std': 10, 'sky_cov_frac': 0.5,
                                       'period': 100, 'amplitude': 0}])

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)

    # Do the dance ...
    chunk.find_slices()
    chunk.find_groups()
    chunk.find_layers()

    # Assert the final METAR code is correct
    assert chunk.metar_msg() == 'SCT009 SCT019'


def test_layering_singlepts():
    """ Test the layering step when there is a single time steps. See #62 for the motivation. """

    mock_data = pd.DataFrame(np.array([['dummy', -1, 2300, 1],
                                       ['dummy', -1, 4000, 2],
                                       ['dummy', -1, 4500, 3],
                                       ['dummy', -1, np.nan, 0]]),
                             columns=['ceilo', 'dt', 'alt', 'type'])

    # Set the proper column types
    for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
        mock_data[col] = mock_data.loc[:, col].astype(tpe)

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)

    # Do the dance ...
    chunk.find_slices()
    chunk.find_groups()
    chunk.find_layers()

    # Check that the GMM was never executed
    assert np.all(chunk.groups.loc[:, 'ncomp'] == -1)
    # Check that the resulting layers and groups are the same
    assert np.all(chunk.groups.loc[:, 'code'] == chunk.layers.loc[:, 'code'])


def test_layering_singleval():
    """ Test the layering step when there is a single altitude value. See #76 for details. """

    data = np.array([np.ones(30), np.arange(0, 30, 1), np.ones(30)*170000, np.ones(30)])

    mock_data = pd.DataFrame(data.T,
                             columns=['ceilo', 'dt', 'alt', 'type'])

    # Set the proper column types
    for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
        mock_data[col] = mock_data.loc[:, col].astype(tpe)

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)

    # Do the dance ...
    chunk.find_slices()
    chunk.find_groups()
    chunk.find_layers()

    # Check that the GMM was never executed
    assert np.all(chunk.groups.loc[:, 'ncomp'] == -1)


def test_coplanar_hull():
    """ Test that the complex hull calculation does not crash the code if points are co-planar. """

    data = np.array([np.ones(10), np.arange(0, 10, 1), np.arange(0, 10, 1), np.ones(10)])

    mock_data = pd.DataFrame(data.T,
                             columns=['ceilo', 'dt', 'alt', 'type'])

    # Set the proper column types
    for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
        mock_data[col] = mock_data.loc[:, col].astype(tpe)

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)

    # Do the dance ...
    chunk.find_slices()

    # Points are coplanar, the fluffiness should be forced to 0
    assert chunk.slices.loc[0, 'fluffiness'] == 0


def test_layering_dualeval():
    """ Test the layering step when there are two single altitude values. See #78 for details. """

    data1 = np.array([np.ones(30), np.arange(0, 30, 1), np.ones(30)*120, np.ones(30)*1])
    data2 = np.array([np.ones(30), np.arange(0, 30, 1), np.ones(30)*150, np.ones(30)*2])

    mock_data = pd.DataFrame(np.concatenate([data1, data2], axis=1).T,
                             columns=['ceilo', 'dt', 'alt', 'type'])

    # Set the proper column types
    for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
        mock_data[col] = mock_data.loc[:, col].astype(tpe)

    # Instantiate a CeiloChunk entity ...
    chunk = CeiloChunk(mock_data)

    # Do the dance ...
    chunk.find_slices()
    chunk.find_groups()
    # The layering should be solid enough to not complain if there are only two values in the data
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        warnings.simplefilter("default", category=FutureWarning)  # Fixes #87
        chunk.find_layers()
