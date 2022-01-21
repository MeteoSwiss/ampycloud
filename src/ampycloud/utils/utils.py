"""
Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: generic utilities
"""

# Import from Python
import logging
import contextlib
import numpy as np

# Instantiate the module logger
logger = logging.getLogger(__name__)

@contextlib.contextmanager
def tmp_seed(seed : int):
    """ Temporarily reset the :py:func:`numpy.random.seed` value.

    Adapted from the reply of Paul Panzer on `SO <https://stackoverflow.com/questions/49555991/>`__.

    Example:
    ::

        with temp_seed(42):
            np.random.random(1)

    """

    # Add a note in the logs about what is going on
    logger.debug('Setting a temporary np.random.seed with value %i', seed)

    # Get the current seed
    state = np.random.get_state()

    # Reset it with the temporary one
    np.random.seed(seed)

    # Execute stuff, and reset the original seed once all is over.
    try:
        yield
    finally:
        np.random.set_state(state)
