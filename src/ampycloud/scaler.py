"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

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
def shift_and_scale(vals: np.ndarray, shift: Union[int, float, None] = None,
                    scale: Union[int, float] = 1, mode: str = 'do') -> np.ndarray:
    """ Shift (by a constant) and scale (by a constant) the data.

    Args:
        vals (ndarray): values to (un-)shift-and-scale.
        shift (int|float, optional): amount to shift the data by. If not specified, it will be set
            to ``max(vals)``.
        scale (int|float, optional): the scaling value. Defaults to 1.
        mode (str, optional): whether to 'do' or 'undo' the shift-and-scale.

    Returns:
        np.ndarray: the (un-)shifted-and-scaled array.

    This function converts x to (x-shift)/scale if ``mode='do'``, and to x * scale + shift if
    ``mode='undo'``.

    """

    # Let's deal with None shift ... this is important to ensure that the ampycloud algorithm
    # always deals with the respective time separation between measurements, when doing the
    # clustering.
    if shift is None:
        shift = np.nanmax(vals)

    # Implement the scaling routine
    if mode == 'do':
        return (vals-shift)/scale
    if mode == 'undo':
        return vals * scale + shift

    raise AmpycloudError(f'Mode unknown: {mode}')


@log_func_call(logger)
def minmax_scale(vals: np.ndarray,
                 min_val: Union[float, int, None] = None,
                 max_val: Union[float, int, None] = None,
                 mode: str = 'do') -> np.ndarray:
    """ Rescale the data onto a [0, 1] interval, possibly forcing a specific and/or minimum
        interval range.

    Args:
        vals (ndarray): values to (un-)minmax-scale.
        mode (str, optional): whether to 'scale' or 'descale', i.e. undo the scaling.
        min_val (int|float, optional): value to be mapped to 0. If not set, will be ``min(vals)``.
            Defaults to None.
        max_val (int|float, optional): value to be mapped to 1. If not set, will be ``max(vals)``.
            Defaults to None.

    Returns:
        ndarray: The (un-)minmax-scaled array.

    """

    # Compute the "default" edges if warranted
    if min_val is None:
        min_val = np.nanmin(vals)
    if max_val is None:
        max_val = np.nanmax(vals)

    if mode == 'do':
        return (vals-min_val)/(max_val-min_val)

    if mode == 'undo':
        return vals * (max_val - min_val) + min_val

    raise AmpycloudError(f'Mode unknown: {mode}')


@log_func_call(logger)
def minrange2minmax(vals: np.ndarray, min_range: Union[int, float] = 0) -> tuple:
    """ Transform a minimum range into a pair of min/max values.

    Args:
        vals (np.ndarray): values to assess.
        min_range (int|float, optional): mininum range to meet. Defaults to 0.

    Returns:
        tuple: the min and max values of the data range of at least min_range in size.

    Essentially, if max(vals)-min(vals) >= min_range, this function returns
    ``[min(vals), max(vals)]``. Else, it returns ``[val_mid-min_range/2, val_mid+min_range/2]``,
    with ```val_mid=(max(vals)+min(vals))/2``.

    """

    val_range = np.nanmax(vals) - np.nanmin(vals)
    if val_range >= min_range:
        return (np.nanmin(vals), np.nanmax(vals))

    # Compute the middle of the data
    val_mid = (np.nanmax(vals) + np.nanmin(vals))/2

    # Build a symetric range around it
    return (val_mid - min_range/2, val_mid + min_range/2)


@log_func_call(logger)
def step_scale(vals: np.ndarray,
               steps: list, scales: list, mode: str = 'do') -> np.ndarray:
    """ Scales values step-wise, with different constants bewteen specific steps.

    Args:
        vals (ndarray): values to scale.
        steps (list, optional): the step **edges**. E.g. [8000, 14000].
        scales (list, optional): the scaling values (=dividers) for each step.
            E.g. [100, 500, 1000]. Must have len(scales) = len(steps)+1.
        mode (str, optional): whether to 'do' or 'undo' the scaling.

    Returns:
        ndarray: (un-)step-scaled values

    Values are divided by scales[i] between steps[i-1:i].
    Anything outside the range of steps is divided by scales[0] or scale[-1].

    Note that this function ensures that each step is properly offseted to ensure that the
    scaled data is continuous (no gaps and no overlapping steps) !

    """

    # Some sanity checks
    if len(steps) != len(scales)-1:
        raise AmpycloudError('Steps and scales have incompatible lengths.')

    if np.any(np.diff(steps) < 0):
        raise AmpycloudError('Steps should be ordered from smallest to largest !')

    # What is the offset of each bin ?
    offsets = [0] + steps

    # Get the bin edges for the scale mode
    edges_in = [-np.inf] + steps + [np.inf]
    # Idem for the descale mode ... this is more complex because of the continuity requirement
    edges_out = [steps[0]/scales[0] + np.sum((np.diff(steps)/scales[1:-1])[:ind])
                 for ind in range(len(steps))]
    edges_out = [-np.inf] + edges_out + [np.inf]

    # Prepare the output
    out = np.full_like(vals, np.nan, dtype=float)

    # Start scaling things, one step after another
    for (sid, sval) in enumerate(scales):

        # What is this specific step offset (to ensure continuity between steps) ?
        if len(steps) > 0:
            cont_corr = np.concatenate((np.array([steps[0]/scales[0]]),
                                        np.diff(steps)/scales[1:-1]))
            cont_corr = np.sum(cont_corr[:sid])
        else:
            cont_corr = 0  # Special case for when I have a single scaling for the entire interval

        if mode == 'do':

            # Which values belong to that step ?
            cond = (edges_in[sid] <= vals) * (vals < edges_in[sid+1])
            # Apply the scaling
            out[cond] = (vals[cond] - offsets[sid])/sval + cont_corr

        elif mode == 'undo':

            # Which value belongs to that step ?
            cond = (vals >= edges_out[sid]) * (vals < edges_out[sid+1])
            # Apply the descaling
            out[cond] = (vals[cond] - cont_corr) * sval + offsets[sid]

        else:
            raise AmpycloudError(f'Mode unknown: {mode}')

    return out


@log_func_call(logger)
def convert_kwargs(vals: np.ndarray, fct: str, **kwargs) -> dict:
    """ Converts the user-input keywords such that they can be fed to the underlying scaling
    functions.

    Args:
        vals (np.ndarray): the values to be processed.
        fct (str): the scaling mode, e.g. 'shift-and-scale', etc ....
        **kwargs: dict of keyword arguments to be converted, if warranted.

    Returns:
        dict: the data-adjusted set of kwargs.

    Note:
        This function was first introduced to accomodate the creation of a secondary axis on the
        ampycloud diagnostic plots. It is a buffer that allows to separate "user" scaling
        keywords from the "deterministic" scaling keywords required to get a specific scaling, no
        matter the underlying dataset (as is required for plotting a secondary axis).

        Essentially, this function allows to feed either "user" or "deterministic" keywords to
        :py:func:`.apply_scaling`, such that the former will be turned into the latter, and the
        latter will remain untouched.

    """

    if fct == 'shift-and-scale':
        # In this case, the only data I may need to derive from the data is the shift.
        if 'shift' in kwargs:
            # Already set - do nothing
            return kwargs
        if 'mode' in kwargs:
            if kwargs['mode'] == 'do':
                kwargs['shift'] = np.nanmax(vals)
            elif kwargs['mode'] == 'undo':
                raise AmpycloudError('I cannot get `shift` from the shift-and-scaled data !')
            else:
                raise AmpycloudError(f"mode unknown: {kwargs['mode']}")
            return kwargs

        # 'mode' is not set -> it will be "do" by default.
        kwargs['shift'] = np.nanmax(vals)
        return kwargs

    if fct == 'minmax-scale':
        # In this case, the challenge lies with identifying min_val and max_val, knowing that the
        # user may specify a min_range value.
        if 'min_val' in kwargs and 'max_val' in kwargs:
            # Already specified ... do  nothing
            return kwargs
        if 'mode' in kwargs:
            if kwargs['mode'] == 'do':
                if 'min_range' in kwargs:
                    min_range = kwargs['min_range']
                    kwargs.pop('min_range', None)
                else:
                    min_range = 0
                (kwargs['min_val'], kwargs['max_val']) = minrange2minmax(vals, min_range)
                return kwargs

            if kwargs['mode'] == 'undo':
                raise AmpycloudError('I cannot get `min_val` and `max_val` from' +
                                     ' minmax-scaled data !')

            raise AmpycloudError(f"Mode unknown: {kwargs['mode']}")

        # 'mode' not set -> will default to 'do'
        if 'min_range' in kwargs:
            min_range = kwargs['min_range']
            kwargs.pop('min_range', None)
        else:
            min_range = 0
        (kwargs['min_val'], kwargs['max_val']) = minrange2minmax(vals, min_range)
        return kwargs

    if fct == 'step-scale':
        # Nothing to be done here
        return kwargs

    raise AmpycloudError(f'Scaling fct unknown: {fct}')


@log_func_call(logger)
def apply_scaling(vals: np.ndarray, fct: Union[str, None] = None, **kwargs) -> np.ndarray:
    """ Umbrella scaling routine, that gathers all the individual ones under a single entry point.

    Args:
        vals (ndarray): values to scale.
        fct (str, optional): name of the scaling function to use. Can be one of
            ['shift-and-scale', 'minmax-scale', or 'step-scale']. Defaults to None = do nothing.
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

    # Process the user-supplied kwargs into kwargs I can feed the functions.
    kwargs = convert_kwargs(vals, fct, **kwargs)

    if fct == 'shift-and-scale':
        return shift_and_scale(vals, **kwargs)

    if fct == 'minmax-scale':
        return minmax_scale(vals, **kwargs)

    if fct == 'step-scale':
        return step_scale(vals, **kwargs)

    raise AmpycloudError(f'Scaling function name unknown: {fct}')
