"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the version module
"""

# Import from Python
import packaging

# Import from this package
from ampycloud.version import VERSION


def test_version():
    """ Test the format of the code version."""

    assert isinstance(VERSION, str)
    # Here, let's make sure the version is valid. One way to check this is to make sure that it is
    # not converted into a LegacyVersion. Any valid version should be greater than 0.
    # Only LegacyVersion wouldn't.
    # Not the most elegant, but better than nothing.
    assert packaging.version.parse(VERSION) > packaging.version.parse('0')
