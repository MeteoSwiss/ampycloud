"""
Copyright (c) 2021-2026 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the wmo module. Check perc2okta consistency with
    Boers, R., de Haij, M. J., Wauben, W. M. F., Baltink, H. K., van Ulft, L. H.,
    Savenije, M., and Long, C. N. (2010), Optimized fractional cloudiness determination
    from five ground-based remote sensing techniques, J. Geophys. Res., 115, D24116,
    `doi:10.1029/2010JD014661 <https://doi.org/10.1029/2010JD014661>`_.
"""

import pytest
from numpy import array, ndarray

from ampycloud.errors import AmpycloudError
from ampycloud.wmo import perc2okta, height2code


@pytest.mark.parametrize(
    "val,expected_okta",
    [
        pytest.param(0, 0, id="exact boundary 0"),
        pytest.param(1e-9, 1, id="just above 0"),
        pytest.param(18.75 - 1e-9, 1, id="just below 18.75"),
        pytest.param(31.25 - 1e-9, 2, id="just below 31.25"),
        pytest.param(43.75 - 1e-9, 3, id="just below 43.75"),
        pytest.param(56.25 - 1e-9, 4, id="just below 56.25"),
        pytest.param(68.75 - 1e-9, 5, id="just below 68.75"),
        pytest.param(81.25 - 1e-9, 6, id="just below 81.25"),
        pytest.param(100 - 1e-9, 7, id="just below 100"),
        pytest.param(18.75, 2, id="exact boundary 18.75"),
        pytest.param(31.25, 3, id="exact boundary 31.25"),
        pytest.param(43.75, 4, id="exact boundary 43.75"),
        pytest.param(56.25, 5, id="exact boundary 56.25"),
        pytest.param(68.75, 6, id="exact boundary 68.75"),
        pytest.param(81.25, 7, id="exact boundary 81.25"),
        pytest.param(100, 8, id="exact boundary 100"),
    ],
)
def test_perc2okta_scalar(val: float, expected_okta: int):
    """Test perc2okta() for scalar inputs"""

    # when
    out = perc2okta(val)

    # then
    assert isinstance(out, ndarray)
    assert out.item() == expected_okta


@pytest.mark.parametrize(
    "vals,okta",
    [
        pytest.param([0, 10, 20, 35, 45, 60, 70, 85, 100], [0, 1, 2, 3, 4, 5, 6, 7, 8], id="typical values"),
        pytest.param([6.15, 24.94, 37.51, 50.03, 62.56, 75.18, 95.07], [1, 2, 3, 4, 5, 6, 7], id="realistic samples"),
    ],
)
def test_perc2okta_array(vals: list[float], okta: list[int]):
    """Test that perc2okta() is properly vectorized"""

    # when
    result = perc2okta(array(vals))

    # then
    assert (result == array(okta)).all()


@pytest.mark.parametrize(
    "val",
    [
        pytest.param(-1, id="below 0"),
        pytest.param(101, id="above 100"),
        pytest.param(-0.0001, id="just below 0"),
        pytest.param(100.0001, id="just above 100"),
    ],
)
def test_perc2okta_invalid(val: float):
    """Test that out-of-range values raise an AmpycloudError."""

    with pytest.raises(AmpycloudError):
        perc2okta(val)


@pytest.mark.parametrize(
    "val,expected_code",
    [
        pytest.param(99.9, "000", id="floor below 100ft"),
        pytest.param(100, "001", id="floor at 100ft"),
        pytest.param(5555, "055", id="floor below 10'000ft"),
        pytest.param(12345, "120", id="floor above 10'000ft"),
    ],
)
def test_height2code(val: float, expected_code: str):
    """Test the height2code function, including the descaling mode above 10'000ft."""

    code = height2code(val)
    assert code == expected_code
