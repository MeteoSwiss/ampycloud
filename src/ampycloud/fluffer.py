"""
Copyright (c) 2021-2024 MeteoSwiss, contributors listed in AUTHORS.

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
        pts (ndarray): 2D array of [dt, height] ceilometer hits. None must have NaNs heights.
        **kwargs (optional): additional arguments to be fed to statsmodels.nonparameteric.lowess().

    Returns:
        float, ndarray: the fluffiness (in height units) and LOWESS-smoothed (dt, height) values
            (sorted).

    The *fluffiness* is computed as `2 * mean(abs(y - lowess))`, where lowess is the smooth
    LOWESS fit to the ceilometer hits.

    The factor 2 stems from the fact that abs(y-lowess) corresponds to half(-ish) the slice
    thickness, that needs to be doubled in order to use the fluffiness to rescale the slice onto the
    0 - 1 range.

    To avoid LOWESS warning, hits with identical x coordinates (= time steps) are being offset
    by a small factor (1e-5).
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
        # Let's add (ind * 1e-5) to any duplicated point. We use the point index "ind"
        # to make sure tri-/quadru-/multi-ple points all get shifted to distinct
        # positions.
        unique_xs = [pts[0, 0]] + [item if diffs[ind] > 0 else item + (ind + 1) * 1e-5
                                   for (ind, item) in enumerate(pts[1:, 0])]
        unique_xs = np.array(unique_xs)

    # For more points, actually do some work
    lowess_pts = sm.nonparametric.lowess(pts[:, 1], unique_xs, return_sorted=True,
                                         is_sorted=True, missing='none', **kwargs)

    fluffiness = 2 * np.mean(np.abs(pts[:, 1] - lowess_pts[:, 1]))
    return fluffiness, lowess_pts
