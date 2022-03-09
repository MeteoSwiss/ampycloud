"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the dynamic module
"""


# Import from ampycloud
from ampycloud import dynamic, reset_prms


def test_dynamic_module():
    """ Test the dynamic module, and in particular the abilty to set those parameters
    interactively if/when needed. """

    # Check that I can set a value and store it just fine.
    val_orig = dynamic.AMPYCLOUD_PRMS['OKTA_LIM0']
    dynamic.AMPYCLOUD_PRMS['OKTA_LIM8'] = -1
    new_val = dynamic.AMPYCLOUD_PRMS['OKTA_LIM8']

    assert 0 <= val_orig <= 100
    assert val_orig != new_val
    assert new_val == -1

    # Check whether I can copy PRMS values and change these without altering the originals
    # (i.e do I need a deepcopy ?)
    tmp = dynamic.AMPYCLOUD_PRMS['MPL_STYLE']
    assert tmp == dynamic.AMPYCLOUD_PRMS['MPL_STYLE']
    tmp = 'bad'
    assert dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] != 'bad'
    assert tmp == 'bad'

    # Also test with new dictionnary keys, that seems to behave differently
    tmp = {}
    tmp.update(dynamic.AMPYCLOUD_PRMS['SLICING_PRMS']['dt_scale_kwargs'])
    tmp['new_entry'] = 'rubbish'
    assert 'new_entry' in tmp.keys()
    assert 'new_entry' not in dynamic.AMPYCLOUD_PRMS['SLICING_PRMS']['dt_scale_kwargs'].keys()

    # Reset everything so as to not break havoc with the other tests
    reset_prms()
