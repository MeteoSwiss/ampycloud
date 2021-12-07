"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: data scaling tools
"""

# Import from Python
from typing import Union
import logging
import numpy as np

# Import from ampycloud
from .errors import AmpycloudError
from .logger import log_func_call

# Instantiate the module logger
logger = logging.getLogger(__name__)

@log_func_call(logger)
def const_scaling(vals : np.ndarray,
                  scale : Union[int, float], mode : str = 'scale') -> np.ndarray:
    """ Scale (or descale) values by a constant.

    Args:
        vals (ndarray): values to (de-)scale.
        scale (int|float): the scaling value.
        mode (str, optional): whether to 'scale' or 'descale', i.e. undo the scaling.

    Returns:
        ndarray: vals/scale if mode=='scale', and val * scale if mode=='descale'.
    """

    if mode == 'scale':
        return vals/scale

    if mode == 'descale':
        return vals * scale

    raise AmpycloudError(f' Ouch ! mode unknown: {mode}')

@log_func_call(logger)
def minmax_scaling(vals : np.ndarray,
                   min_range : Union[float, int] = 0,
                   mode : str = 'scale',
                   min_val : Union[float, int] = None,
                   max_val : Union[float, int] = None) -> np.ndarray:
    """ Rescale the data onto a [0, 1] interval, possibly using a minimum interval range.

    Note:
        Descaling with this function is a little bit annoying, because the data itself does not
        contain enough information to know what interval vals should be mapped onto.
        Hence the min_val and max_val kwargs, so that the user can tell us ...

    Args:
        vals (ndarray): values to (de-)scale.
        min_range (int|float, optional): will map the [0, 1] interval to
            [val_mid-min_range/2, val_mid+min_range/2] rather than [val_min, val_max],
            if val_max-val_min < min_range. Note: val_mid=(val_max+val_min)/2.
        mode (str, optional): whether to 'scale' or 'descale', i.e. undo the scaling.
        min_val (int|float, optional): min (target) interval value, in case mode='descale'.
            Defaults to None.
        max_val (int|float, optional): max (target) interval value, in case mode='descale'.
            Defaults to None.

    Returns:
        ndarray: scaled/descaled values.


    """

    if mode == 'scale':
        # What is the range of the data
        val_range = np.nanmax(vals) - np.nanmin(vals)
        val_mid = (np.nanmax(vals) + np.nanmin(vals))/2

        # Deal with the cases where all the values are the same by returning nans
        if val_range == 0:
            return vals * np.nan

        # Else, deal with the values as usual ...
        if val_range >= min_range:
            mymax = np.nanmax(vals)
            mymin = np.nanmin(vals)
        # ... unless I have a range smaller than the min_range specified by the user.
        else:
            mymax = val_mid + min_range/2
            mymin = val_mid - min_range/2

        return (vals-mymin)/(mymax-mymin)

    if mode == 'descale':
        # Compute the original range and mid point
        val_range = max_val - min_val
        val_mid = (max_val + min_val)/2

        # Descale, properly handling the case where min_range matters.
        if val_range >= min_range:
            return vals * (max_val - min_val) + min_val

        return vals * min_range + (val_mid - min_range/2)

    raise AmpycloudError(f' Ouch ! mode unknown: {mode}')

@log_func_call(logger)
def step_scaling(vals : np.ndarray,
                 steps : list, scales : list, mode : str = 'scale') -> np.ndarray:
    """ Scales values step-wise, with different constants bewteen specific steps.

    Values are scaled by scales[i] between steps[i-1:i].
    Anything outside the range of steps is scaled by scales[0] or scale[-1].

    Note that this function ensures that each step is properly offseted to ensure that the
    scaled data is continuous !

    Args:
        vals (ndarray): values to scale.
        steps (list, optional): the step **edges**. E.g. [8000, 14000].
        scales (list, optional): the scaling values for each step. E.g. [100, 500, 1000].
            Must have len(scales) = len(steps)+1.
        mode (str, optional): whether to 'scale' or 'descale', i.e. undo the scaling.

    Returns:
        ndarray: (de-)scaled values
    """

    # Some sanity checks
    if len(steps) != len(scales)-1:
        raise AmpycloudError('Ouch ! steps and scales have incompatible lengths.')

    if np.any(np.diff(steps) < 0):
        raise AmpycloudError('Ouch ! steps should be oredered from smallest to largest !')

    # What is the offset of each bin ?
    offsets = [0] + steps

    # Get the bin edges for the scale mode
    edges_in = [-np.infty] + steps + [np.infty]
    # Idem for the descale mode ... this is more complex because of the continuity requirement
    edges_out = [steps[0]/scales[0] + np.sum((np.diff(steps)/scales[1:-1])[:ind])
                 for ind in range(len(steps))]
    edges_out = [-np.infty] + edges_out + [np.infty]

    # Prepare the output
    out = np.full_like(vals, np.nan, dtype=float)

    # Start scaling things, one step after another
    for (sid, scale) in enumerate(scales):

        # What is this specific step offset (to ensure continuitiy between steps) ?
        cont_corr = np.concatenate((np.array([steps[0]/scales[0]]), np.diff(steps)/scales[1:-1]))
        cont_corr = np.sum(cont_corr[:sid])

        if mode == 'scale':

            # Which values belong to that step ?
            cond = (edges_in[sid] <= vals) * (vals < edges_in[sid+1])
            # Apply the scaling
            out[cond] = (vals[cond] - offsets[sid])/scale + cont_corr

        if mode == 'descale':

            # Which value belongs to that step ?
            cond = (vals >= edges_out[sid]) * (vals < edges_out[sid+1])
            # Apply the descaling
            out[cond] = (vals[cond] - cont_corr) * scale + offsets[sid]

    return out

@log_func_call(logger)
def scaling(vals : np.ndarray, fct : str = None, **kwargs) -> np.ndarray:
    """ Umbrella scaling routine, that gathers all the individual ones under a single entry point.

    Args:
        vals (ndarray): values to scale.
        fct (str, optional): name of the scaling function to use. Can be one of
            ['const', 'minmax', or 'step']. Defaults to None =  do nothing.
        **kwargs: keyword arguments that will be fed to the underlying scaling function.

    Returns:
        ndarray: the scaled values.
    """

    # If I was asked to do nothing, then do nothing ...
    if fct is None:
        return vals

    # If I only get NaNs, return NaNs
    if np.all(np.isnan(vals)):
        return vals

    if fct == 'const':
        return const_scaling(vals, **kwargs)

    if fct == 'minmax':
        return minmax_scaling(vals, **kwargs)

    if fct == 'step':
        return step_scaling(vals, **kwargs)

    raise AmpycloudError(f'Ouch ! Scaling function name unknown: {fct}')
