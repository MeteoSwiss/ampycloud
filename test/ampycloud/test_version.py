"""
Copyright (c) 2021-2026 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the version module
"""

# Import from Python
import importlib
from importlib.metadata import PackageNotFoundError

import pytest

# Import from this package
import ampycloud.version as version_module


@pytest.fixture
def restore_version_module():
    """Reload ampycloud.version after the test, undoing any monkeypatched reload."""
    yield
    importlib.reload(version_module)


def test_version_reads_installed_metadata(monkeypatch, restore_version_module):
    """Test that VERSION picks up whatever importlib.metadata reports as installed."""
    monkeypatch.setattr("importlib.metadata.version", lambda name: "9.9.9")
    reloaded = importlib.reload(version_module)
    assert reloaded.VERSION == "9.9.9"


def test_version_falls_back_to_placeholder_when_not_installed(monkeypatch, restore_version_module):
    """Test that VERSION falls back to the 0.0.0 placeholder when the package isn't installed."""

    def _raise(name):
        raise PackageNotFoundError(name)

    monkeypatch.setattr("importlib.metadata.version", _raise)
    reloaded = importlib.reload(version_module)
    assert reloaded.VERSION == "0.0.0"
