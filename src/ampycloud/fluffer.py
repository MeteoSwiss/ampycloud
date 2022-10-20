"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: fluffiness-related tools
"""

# Import from Python
import logging
import numpy as np
import statsmodels.api as sm

# Import from this package
from .logger import log_func_call
from .errors import AmpycloudError


# Instantiate the module logger
logger = logging.getLogger(__name__)


@log_func_call(logger)
def get_fluffiness(pts, **kwargs):
    """ Utility functions to compute the fluffiness of a set of ceilometer hits.

    Args:
        pts (ndarray): 2D array of [dt, alt] ceilometer hits. None must have NaNs altitudes.
         (float): time resolution (in s) to derive the LOWESS frac value, assuming a uniform
            density of points over the interval.
        **kwargs (optional): additional arguments to be fed to statsmodels.nonparameteric.lowess().

    Returns:
        float, ndarray: the fluffiness (in alt units) and LOWESS-smoothed (dt, alt) values (sorted).
    """

    if pts.ndim != 2:
        raise AmpycloudError('pts should be 2-dimensional.')

    # If I was given a single point, things are easy
    if len(pts) == 1:
        return 0, pts

    # Begin by sorting points if they are not already - I'll need this to compute the fluffiness
    pts = pts[pts[:, 0].argsort()]

    # Points with duplicated x values trigger a RuntimeWarning from LOWESS.
    # To avoid it, let's jiggle duplicated points a little bit.
    if len(np.unique(pts[:, 0])) == len(pts):
        unique_xs = pts[:, 0]
    else:
        diffs = np.diff(pts[:, 0])
        unique_xs = [pts[0, 0]] + [item if diffs[ind] > 0 else item + (ind + 1) * 1e-5
                                   for (ind, item) in enumerate(pts[1:, 0])]
        unique_xs = np.array(unique_xs)

    # For more points, actually do some work
    lowess_pts = sm.nonparametric.lowess(pts[:, 1], unique_xs, return_sorted=True,
                                         is_sorted=True, missing='none', **kwargs)

    fluffiness = np.mean(np.abs(pts[:, 1] - lowess_pts[:, 1]))
    return fluffiness, lowess_pts
