"""
Copyright (c) 2021-2026 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the version module
"""

# Import from Python
import pytest
import packaging

# Import from this package
from ampycloud.version import VERSION


def test_version_is_string():
    assert isinstance(VERSION, str)


@pytest.mark.skipif(VERSION == "0.0.0", reason="Skip version > 0 check in dev (placeholder version)")
def test_version_greater_than_zero():
    """Test that VERSION > 0 (only in CI with real version)."""
    # Here, let's make sure the version is valid. One way to check this is to make sure that it is
    # not converted into a LegacyVersion. Any valid version should be greater than 0.
    # Only LegacyVersion wouldn't.
    # Not the most elegant, but better than nothing.
    assert packaging.version.parse(VERSION) > packaging.version.parse("0")


@pytest.mark.skipif(VERSION != "0.0.0", reason="Only check placeholder version in dev")
def test_version_is_placeholder_in_dev():
    """Test that VERSION is 0.0.0 in dev environment."""
    assert VERSION == "0.0.0"
