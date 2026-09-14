"""
Copyright (c) 2021-2026 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the wmo module
"""

import numpy as np
import pytest

from ampycloud.errors import AmpycloudError
from ampycloud.wmo import perc2okta, height2code


def test_perc2okta():
    """Test the perc2okta function. Check consistency with
        Boers, R., de Haij, M. J., Wauben, W. M. F., Baltink, H. K., van Ulft, L. H.,
        Savenije, M., and Long, C. N. (2010), Optimized fractional cloudiness determination
        from five ground-based remote sensing techniques, J. Geophys. Res., 115, D24116,
        `doi:10.1029/2010JD014661 <https://doi.org/10.1029/2010JD014661>`_.
    """

    # perc2okta always returns a ndarray, even for scalar input.
    assert isinstance(perc2okta(43), np.ndarray)

    # The two exact edge cases.
    assert np.all(perc2okta(0) == np.array([0]))
    assert np.all(perc2okta(100) == np.array([8]))

    # A simple scalar case.
    assert np.all(perc2okta(2) == np.array([1]))

    # One "typical" value per okta bin.
    vals = np.array([0, 10, 20, 35, 45, 60, 70, 85, 100])
    okta = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8])
    assert np.all(perc2okta(vals) == okta)

    # The exact bin boundaries: each bin is [lower, upper), i.e. the lower bound belongs to
    # the bin, while the upper bound belongs to the *next* bin.
    bounds = np.array([0, 18.75, 31.25, 43.75, 56.25, 68.75, 81.25, 100])
    okta = np.array([0, 2, 3, 4, 5, 6, 7, 8])
    assert np.all(perc2okta(bounds) == okta)

    # A value just *below* each upper bound should still belong to the lower okta bin.
    just_below = bounds - 1e-9
    just_below[0] = 1e-9  # val=0 is the special case: there is no "just below" 0.
    okta_below = np.array([1, 1, 2, 3, 4, 5, 6, 7])
    assert np.all(perc2okta(just_below) == okta_below)

    # Sample values drawn from within each bin (mimicking realistic sensor readings).
    samples = np.array([6.15, 24.94, 37.51, 50.03, 62.56, 75.18, 95.07])
    okta_samples = np.array([1, 2, 3, 4, 5, 6, 7])
    assert np.all(perc2okta(samples) == okta_samples)

    # Out-of-range values must raise an AmpycloudError.
    with pytest.raises(AmpycloudError):
        perc2okta(-1)
    with pytest.raises(AmpycloudError):
        perc2okta(101)


def test_height2code():
    """Test the alt2code function, inculding the descaling mode."""

    assert height2code(99.9) == "000"
    assert height2code(100) == "001"
    assert height2code(5555) == "055"
    assert height2code(12345) == "120"
