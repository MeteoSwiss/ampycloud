"""
Copyright (c) 2021-2024 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the utils.utils module
"""

# Import form Python
import warnings
from pytest import mark, param, raises, warns
import numpy as np
import pandas as pd

# Import from ampycloud
from ampycloud.utils.utils import (check_data_consistency, tmp_seed,
                                   adjust_nested_dict, calc_base_height)
from ampycloud.utils.mocker import canonical_demo_data
from ampycloud.errors import AmpycloudError, AmpycloudWarning
from ampycloud import hardcoded


def test_check_data_consistency():
    """ This routine tests the check_data_consistency method. """

    # The following should not trigger any warning... let's make sure of that.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        warnings.simplefilter("default", category=FutureWarning)  # Fixes #87
        out = check_data_consistency(canonical_demo_data())

        # Make sure the canonical demo data is perfectly compatible with the ampycloud requirements
        assert np.all(out == canonical_demo_data())

    # Now, let's check specific elements that should raise errors or warnings
    ### ERRORS ###
    with raises(AmpycloudError):
        # Empty DataFrame
        data = pd.DataFrame(columns=['ceilo', 'dt', 'height', 'type'])
        check_data_consistency(data)
    with raises(AmpycloudError):
        # Missing column
        data = pd.DataFrame(np.array([['a', 1, 1]]), columns=['ceilo', 'height', 'type'])
        for col in ['ceilo', 'height', 'type']:
            data[col] = data.loc[:, col].astype(hardcoded.REQ_DATA_COLS[col])
        check_data_consistency(data)
    with raises(AmpycloudError):
        # Duplicated hit
        data = pd.DataFrame(np.array([['a', 0., 1, 1], ['a', 0., 1, 1]]),
                            columns=['ceilo', 'dt', 'height', 'type'])
        for col in ['ceilo', 'dt', 'height', 'type']:
            data[col] = data.loc[:, col].astype(hardcoded.REQ_DATA_COLS[col])
        check_data_consistency(data)
    with raises(AmpycloudError):
        # Inconsistent hits - type 0 vs type !0
        data = pd.DataFrame(np.array([['a', 0, 1, 1], ['a', 0, np.nan, 0]]),
                            columns=['ceilo', 'dt', 'height', 'type'])
        for col in ['ceilo', 'dt', 'height', 'type']:
            data[col] = data.loc[:, col].astype(hardcoded.REQ_DATA_COLS[col])
        check_data_consistency(data)
    with raises(AmpycloudError):
        # Inconsistent vv hits - it must be either a VV hit, or a hit, but not both.
        data = pd.DataFrame(np.array([['a', 0, 1, -1], ['a', 0, 2, 1]]),
                            columns=['ceilo', 'dt', 'height', 'type'])
        for col in ['ceilo', 'dt', 'height', 'type']:
            data[col] = data.loc[:, col].astype(hardcoded.REQ_DATA_COLS[col])
        check_data_consistency(data)

    # The following should NOT raise an error, i.e. two simultaneous hits from *distinct* parameters
    data = pd.DataFrame(np.array([['a', 0, 1, -1], ['b', 0, np.nan, 0]]),
                        columns=['ceilo', 'dt', 'height', 'type'])
    for col in ['ceilo', 'dt', 'height', 'type']:
        data[col] = data.loc[:, col].astype(hardcoded.REQ_DATA_COLS[col])
    check_data_consistency(data)

    ### WARNINGS ###
    with warns(AmpycloudWarning):
        # Bad data type
        data = pd.DataFrame(np.array([['a', 0, 1, 1]]), columns=['ceilo', 'dt', 'height', 'type'])
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Extra key
        data = pd.DataFrame(np.array([['a', 0, 1, 1, 99]]),
                            columns=['ceilo', 'dt', 'height', 'type', 'extra'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data[col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Negative heights
        data = pd.DataFrame(np.array([['a', 0, -1, 1]]),
                            columns=['ceilo', 'dt', 'height', 'type'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data[col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Type 0 should be NaN
        data = pd.DataFrame(np.array([['a', 0, 1, 0]]),
                            columns=['ceilo', 'dt', 'height', 'type'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data[col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Type 1 should not be NaN
        data = pd.DataFrame(np.array([['a', 0, np.nan, 1]]),
                            columns=['ceilo', 'dt', 'height', 'type'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data[col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Missing type 1 pts
        data = pd.DataFrame(np.array([['a', 0, 1, 2]]),
                            columns=['ceilo', 'dt', 'height', 'type'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data[col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Missing type 2 pts
        data = pd.DataFrame(np.array([['a', 0, 1, 3]]),
                            columns=['ceilo', 'dt', 'height', 'type'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data[col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)


def test_tmp_seed():
    """ This routine tests the tmp_seed. """

    # Let's set a seed, get some random numbers, then check if I can reproduce this with tmp_seed.
    np.random.seed(42)
    a = np.random.random(100)
    b = np.random.random(10)
    c = np.random.random(1)

    # Make sure I get the concept of random numbers ...
    np.random.seed(43)
    a43 = np.random.random(100)
    assert np.all(a != a43)

    np.random.seed(42)
    a42 = np.random.random(100)
    assert np.all(a == a42)

    # Now, actually check the function I am interested in.
    np.random.seed(43)  # Set a seed
    with tmp_seed(42):  # Temporarily set anopther one
        assert np.all(a == np.random.random(100))
        assert np.all(b == np.random.random(10))
        assert np.all(c == np.random.random(1))

    # Can I recover the original seed ?
    assert np.all(a43 == np.random.random(100))


def test_adjust_nested_dict():
    """ This routine tests the adjust_nested_dict function. """

    ref_dict = {'a': 0, 'b': {1: {0}}}
    new_dict = {'a': 1}

    out = adjust_nested_dict(ref_dict, new_dict)
    assert out['a'] == 1
    assert out['b'] == ref_dict['b']

    # Setting a non-pre-existing key should raise an Warning
    with warns(AmpycloudWarning):
        out = adjust_nested_dict(ref_dict, {'b': {'d': {0}}})
        assert out == ref_dict

    new_dict = {'a': [1, 2, 3], 'b': {1: {2}}}
    out = adjust_nested_dict(ref_dict, new_dict)
    assert out == new_dict


@mark.parametrize('lookback_perc,height_perc,q_expected', [
    param(50, 90, 95, id='both params'),
    param(100, 98, 98, id='height_perc only'),
    param(42, 100, 100., id='lookback_only'),
])
def test_calc_base_height(
        lookback_perc: int,
        height_perc: int,
        q_expected: np.float64,
    ):
        """Test the calculation of the slice/ group/ layer base height."""
        vals = np.arange(1., 101.)
        q = calc_base_height(vals, lookback_perc, height_perc)
        np.testing.assert_almost_equal(q, q_expected, decimal=1)
