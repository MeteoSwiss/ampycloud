"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the version module
"""

# Import from this package
from ampycloud.version import VERSION

def test_version():
    """ Test the format of the code version."""

    assert isinstance(VERSION, str)
    assert len(VERSION.split('.'))==3
