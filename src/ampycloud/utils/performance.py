"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: tools to assess the performance of ampycloud
"""

# Import from Python
import logging
from datetime import datetime
import numpy as np

# Import from ampycloud
from ..logger import log_func_call
from ..core import demo

# Instantiate the module logger
logger = logging.getLogger(__name__)


@log_func_call(logger)
def get_speed_benchmark(niter: int = 10) -> tuple:
    """ This function will run and time :py:func:`ampycloud.core.demo` to assess the code's
    performance on a given machine.

    For now, this is a rather dumb and uninspired way to do it. If the need ever arises, this
    could certainly be done better, and (for example) also with a finer step resolution to see
    which step (slicing, grouping, layering) is the slowest, and also separate the generation of
    the mock dataset from its processing.

    Returns:
        int, float, float, float, float, float: niter, mean, std, median, min, max, all in s.

    """

    dts = []

    # Simply run the demo routine n times and monitor the lentgh
    for _ in range(niter):
        start = datetime.now()
        _, _ = demo()
        dts += [(datetime.now()-start).total_seconds()]

    logger.info('ampycloud demo() exec-time from %i runs:', niter)
    logger.info('    mean [std]: %.2fs [%.2fs]', np.mean(dts), np.std(dts))
    logger.info('    median [min; max]: %.2f [%.2fs; %.2fs]',
                np.median(dts), np.min(dts), np.max(dts))

    # Compute some statistics
    return niter, np.mean(dts), np.std(dts), np.median(dts), np.min(dts), np.max(dts)
