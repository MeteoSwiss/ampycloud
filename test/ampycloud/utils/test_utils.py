"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the utils.utils module
"""

# Import form Python
import warnings
from pytest import raises, warns
import numpy as np
import pandas as pd

# Import from ampycloud
from ampycloud.utils.utils import check_data_consistency, tmp_seed, adjust_nested_dict
from ampycloud.utils.mocker import canonical_demo_data
from ampycloud.errors import AmpycloudError, AmpycloudWarning
from ampycloud import hardcoded

def test_check_data_consistency():
    """ This routine tests the check_data_consistency method. """

    # The following should not trigger any warning... let's make sure of that.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        out = check_data_consistency(canonical_demo_data())

        # Make sure the canonical demo data is perfectly compatible with the ampycloud requirements
        assert np.all(out == canonical_demo_data())

    # Now, let's check specific elements that should raise errors or warnings
    with raises(AmpycloudError):
        # Empty DataFrame
        data = pd.DataFrame(columns=['ceilo', 'dt', 'alt', 'type'])
        check_data_consistency(data)
    with raises(AmpycloudError):
        # Missing column
        data = pd.DataFrame(np.array([['a', 1, 1]]), columns=['ceilo', 'alt', 'type'])
        for col in ['ceilo', 'alt', 'type']:
            data.loc[:, col] = data.loc[:,col].astype(hardcoded.REQ_DATA_COLS[col])
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Bad data type
        data = pd.DataFrame(np.array([['a', 0, 1, 1]]), columns=['ceilo', 'dt', 'alt', 'type'])
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Extra key
        data = pd.DataFrame(np.array([['a', 0, 1, 1, 99]]),
                            columns=['ceilo', 'dt', 'alt', 'type', 'extra'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data.loc[:, col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Negative alts
        data = pd.DataFrame(np.array([['a', 0, -1, 1]]),
                            columns=['ceilo', 'dt', 'alt', 'type'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data.loc[:, col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Type 0 should be NaN
        data = pd.DataFrame(np.array([['a', 0, 1, 0]]),
                            columns=['ceilo', 'dt', 'alt', 'type'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data.loc[:, col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Type 1 should not be NaN
        data = pd.DataFrame(np.array([['a', 0, np.nan, 1]]),
                            columns=['ceilo', 'dt', 'alt', 'type'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data.loc[:, col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Missing type 1 pts
        data = pd.DataFrame(np.array([['a', 0, 1, 2]]),
                            columns=['ceilo', 'dt', 'alt', 'type'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data.loc[:, col] = data.loc[:, col].astype(tpe)
        check_data_consistency(data)
    with warns(AmpycloudWarning):
        # Missing type 2 pts
        data = pd.DataFrame(np.array([['a', 0, 1, 3]]),
                            columns=['ceilo', 'dt', 'alt', 'type'])
        for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
            data.loc[:, col] = data.loc[:, col].astype(tpe)
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
    np.random.seed(43) # Set a seed
    with tmp_seed(42): # Temporarily set anopther one
        assert np.all(a == np.random.random(100))
        assert np.all(b == np.random.random(10))
        assert np.all(c == np.random.random(1))

    # Can I recover the original seed ?
    assert np.all(a43 == np.random.random(100))

def test_adjust_nested_dict():
    """ This routine tests the adjust_nested_dict function. """

    ref_dict = {'a':0, 'b':{1:{0}}}
    new_dict = {'a':1}

    out = adjust_nested_dict(ref_dict, new_dict)
    assert out['a'] == 1
    assert out['b'] == ref_dict['b']

    # Setting a non-pre-existing key should raise an Warning
    with warns(AmpycloudWarning):
        out = adjust_nested_dict(ref_dict, {'b': {'d':{0}}})
        assert out == ref_dict

    new_dict = {'a':[1, 2, 3], 'b':{1:{2}}}
    out = adjust_nested_dict(ref_dict, new_dict)
    assert out == new_dict
