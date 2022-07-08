"""
Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: ICAO-related utilities
"""

# Import from Python
import logging

# Import from ampycloud
from .logger import log_func_call

# Instantiate the module logger
logger = logging.getLogger(__name__)


@log_func_call(logger)
def significant_cloud(oktas: list) -> list:
    """ Assesses which cloud layers in a list are significant, according to the ICAO rules.

    Args:
        oktas (list): the okta count of different cloud layers. **These are assumed to be sorted**
            **from the lowest to the highest cloud layer !**

    Returns:
        list of bool: whether a given layer is significant, or not.

    The ICAO rules applied are as follows:

        * first layer is always reported
        * second layer must be SCT or more (i.e. 3 oktas or more)
        * third layer must be BKN or more (i.e. 5 oktas or more)
        * no more than 3 layers reported (since ampycloud does not deal with CB/TCU)

    Reference:
        Sec. 4.5.4.3 e) & footnote #14 in Table A3-1, Meteorological Service for
        International Air Navigation, Annex 3 to the Convention on International Civil Aviation,
        ICAO, 20th edition, July 2018.

    """

    sig_level = 0
    sig = []
    for okta in oktas:
        # There can be no more than 3 significant cloud layers.
        # See that footnote 14 in the ICAO doc !
        if okta > sig_level and sig.count(True) < 3:
            sig_level += 2
            sig += [True]
        else:
            sig += [False]

    return sig
