"""
Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: ICAO-related utilities
"""

# Import from Python
import logging
import numpy as np

# Import from ampycloud
from .logger import log_func_call

# Instantiate the module logger
logger = logging.getLogger(__name__)

@log_func_call(logger)
def significant_cloud(oktas : list) -> list:
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

    Source: Meteorological Service for International Air Navigation, Annex 3 to the Convention on
    International Civil Aviation, ICAO, 7th edition, July 2010.

    Todo:
        At the moment, there is no limit to the number of significant cloud layers possible. I.e.
        any layer with 5 oktas or more will always be reported. Strictly speaking, the
        ICAO doc does not speciify an upper limit ... right ? See #47.

    """

    sig_level = 0
    sig = []
    for okta in oktas:
        if okta > sig_level:
            sig_level += 2
            # Unless proven otherwise, report all layers that are BKN or more.
            sig_level = np.min([sig_level, 4])
            sig += [True]
        else:
            sig += [False]

    return sig
