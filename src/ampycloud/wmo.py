"""
Copyright (c) 2021-2024 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: WMO-related utilities
"""

# Import from Python
import logging
from typing import Optional, Union
import numpy as np

# Import from ampycloud
from .errors import AmpycloudError
from .logger import log_func_call

# Instantiate the module logger
logger = logging.getLogger(__name__)


@log_func_call(logger)
def perc2okta(val: Union[int, float, np.ndarray]) -> np.ndarray:
    """ Converts a sky coverage percentage into oktas.

    Args:
        val (int|float|ndarray): the sky coverage percentage to convert, in percent.

    Returns:
        ndarray of int: the okta value(s).

    One okta corresponds to 1/8 of the sky covered by clouds. The cases of 0 and 8 oktas are
    special, in that these indicate that the sky is covered at *exactly* 0%, respectively 100%.
    This implies that the 1 okta and 7 okta bins are larger than others.

    Specifically:

        - 0 okta  == val=0
        - 1 okta  == 0 < val <= 1.5*100/8
        - 2 oktas == 1.5*100/8 < val <= 2.5*100/8
        - ...
        - 7 oktas == 6.5*100/8 < val < 100
        - 8 oktas == val=100

    Reference:
        Boers, R., de Haij, M. J., Wauben, W. M. F., Baltink, H. K., van Ulft, L. H.,
        Savenije, M., and Long, C. N. (2010), Optimized fractional cloudiness determination
        from five ground-based remote sensing techniques, J. Geophys. Res., 115, D24116,
        `doi:10.1029/2010JD014661 <https://doi.org/10.1029/2010JD014661>`_.
    """

    # A basic sanity check
    if not np.all((val >= 0) * (val <= 100)):
        raise AmpycloudError(f'I need 0<=val<=100, but I got: {val}')

    # If I did not receive a numpy array, build one to be efficient afterwards ...
    if isinstance(val, (float, int)):
        val = np.array([val])

    # Prepare the out array with floats for now. We will round things later on.
    out = np.full_like(val, -1., dtype=float)

    # Deal with the edge cases first
    out[(val == 0)] = 0
    out[(val == 100)] = 8

    # Now deal with the other cases
    out[out == -1] = val[out == -1]/(100/8)
    # Now we round/floor/ceil as required, remembering that the 1 and 7 okta bins are special.
    out[out < 1] = np.ceil(out[out < 1])
    out[out > 7] = np.floor(out[out > 7])
    # Everything else, we just round as usual
    out = np.round(out)

    # Return ints, to make it clear that we do not work with fractional oktas
    return out.astype(int)


@log_func_call(logger)
def okta2code(val: int) -> Optional[str]:
    """ Convert an okta value to a METAR code.

    Args:
        int: okta value between 0 and 9 (included).

    Returns:
        str: METAR code

    Conversion is as follows:

     - 0 okta => NCD
     - 1-2 oktas => FEW
     - 3-4 oktas => SCT
     - 5-7 oktas => BKN
     - 8 oktas => OVC
     - 9 oktas => None

    """

    # Some sanity checks
    if not isinstance(val, int):
        raise AmpycloudError(f'val should be of type int, not: {type(val)}')

    if val == 0:
        return 'NCD'
    if val in [1, 2]:
        return 'FEW'
    if val in [3, 4]:
        return 'SCT'
    if val in [5, 6, 7]:
        return 'BKN'
    if val == 8:
        return 'OVC'
    if val == 9:
        return None

    raise AmpycloudError(f'okta value not understood: {val}')


@log_func_call(logger)
def okta2symb(val: int, use_metsymb: bool = False) -> str:
    """ Convert an okta value to a LaTeX string, possibly using the metsymb LaTeX package.

    Args:
        int: okta value between 0 and 9 (included).
        use_metsymb (bool, optional): if True, will use the metsymb LaTeX package to draw proper
            okta symbols. If False, returns a digit. Defaults to False.

    Returns:
        str: LaTeX command.

    Note:
        The metsymb LaTeX package is available under: `<https://github.com/MeteoSwiss/metsymb>`_
    """

    # If metsymb is not available, just return a number.
    if not use_metsymb:
        return str(val)

    # If metsymb is available, assign the proper commands !
    if val == 0:
        return r'\zerookta\ '
    if val == 1:
        return r'\oneokta\ '
    if val == 2:
        return r'\twooktas\ '
    if val == 3:
        return r'\threeoktas\ '
    if val == 4:
        return r'\fouroktas\ '
    if val == 5:
        return r'\fiveoktas\ '
    if val == 6:
        return r'\sixoktas\ '
    if val == 7:
        return r'\sevenoktas\ '
    if val == 8:
        return r'\eightoktas\ '
    if val == 9:
        return r'\nineoktas\ '

    raise AmpycloudError(f'okta value not understood: {val}')


@log_func_call(logger)
def height2code(val: Union[int, float]) -> str:
    """ Function that converts a given height in hundreds of ft (3 digit number),
    e.g. 5000 ft -> 050, 500 ft -> 005.

    Args:
        val (int, float): the height to convert, in feet.

    Returns:
        str: the corresponding METAR code chunk

    Below 10'000 ft, the value is floored to the nearest 100 ft. Above 10'000 ft, the value is
    floored to the nearest 1000 ft.

    Reference:
        *Aerodrome Reports and Forecasts, A Users' Handbook to the Codes*, WMO-No.782, 2020 edition.
        `<https://library.wmo.int/?lvl=notice_display&id=716>`_

    Warning:
        Currently, this function does **not** allow to implement EASA's rule AMC1 MET.TR.205(e)(3)
        (i.e. setting a resolution of 50 ft up to 300 ft for aerodromes with established
        low-visibility approach and landing procedures).
        `<https://www.easa.europa.eu/downloads/22100/en>`_

    """

    if np.isnan(val):
        return ''

    # Flooring to 100ft below 10'000ft, and 1000ft above.
    # See WMO's "Aerodrome Reports and Forecasts" documents.
    if val <= 10000:
        out = np.floor(val/100)
    else:
        out = np.floor(val/1000)*10

    return f'{int(out):03}'
