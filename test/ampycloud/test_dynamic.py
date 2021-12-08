"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the dynamic module
"""


# Import from ampycloud
from ampycloud import dynamic


def test_dynamic_module():
    """ Test the dynamic module, and in particular the abilty to set those parameters
    interactively if/when needed. """

    # Check that I can set a value and store it just fine.
    val_orig = dynamic.OKTA_LIM0
    dynamic.OKTA_LIM8 = -1
    new_val = dynamic.OKTA_LIM8

    assert 0 <= val_orig <= 100
    assert val_orig != new_val
    assert new_val == -1
