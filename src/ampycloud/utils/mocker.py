"""
Copyright (c) 2021-2024 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: tools to create mock datasets
"""

# Import from Python
import logging
from typing import Union
import numpy as np
import pandas as pd
from pandas import DataFrame

# import from ampycloud
from ..logger import log_func_call
from ..errors import AmpycloudError
from . import utils
from .. import hardcoded

# Instantiate the module logger
logger = logging.getLogger(__name__)


@log_func_call(logger)
def flat_layer(dts: np.ndarray, height: float, height_std: float,
               sky_cov_frac: float) -> DataFrame:
    """ Generates a mock, flat, Gaussian cloud layer around a given height.

    Args:
        dts (np.array of float): time deltas, in s, for the simulated ceilometer hits.
        height (float): layer mean height, in ft above aerodrome level (aal).
        height_std (float): layer height standard deviation, in ft.
        sky_cov_frac (float): Sky coverage fraction. Random hits will be set to NaN to
            reach this value. Must be 0 <= x <= 1.

    Returns:
        :py:class:`pandas.DataFrame`: the simulated layer with columns ['dt', 'height'].
    """

    # How many points do I need to generate ?
    n_pts = len(dts)

    # Create the storage structure
    out = DataFrame(columns=['dt', 'height'], dtype=float)

    # Generate the random height data
    out['height'] = np.random.normal(loc=height, scale=height_std, size=n_pts)
    # Cleanup any negative heights, if warranted.
    out.loc[out['height'] <= 0, 'height'] = np.nan
    out['dt'] = dts

    # Empty hits to get the requested sky coverage fraction
    # First extract the hits I want to keep ...
    to_keep = out.sample(frac=sky_cov_frac)
    # ... then get rid of the height values everywhere ...
    out.loc[:, 'height'] = np.nan
    # ... and re-set the values I choose to keep.
    out.loc[to_keep.index] = to_keep

    return out


@log_func_call(logger)
def sin_layer(dts: np.ndarray, height: float, height_std: float, sky_cov_frac: float,
              period: Union[int, float], amplitude: Union[int, float]) -> DataFrame:
    """ Generates a sinusoidal cloud layer.

    Args:
        dts (np.array of float): time deltas, in s, for the simulated ceilometer hits.
        height (float): layer mean height, in ft above aerodrome level (aal).
        height_std (float): layer height standard deviation, in ft.
        sky_cov_frac (float, optional): Sky coverage fraction. Random hits will be set to NaN to
            reach this value. Must be 0 <= x <= 1.
        period (int|float): period of the sine-wave, in s.
        amplitude (int|float): amplitude of the sine-wave, in ft.

    Returns:
        :py:class:`pandas.DataFrame`: the simulated layer with columns ['height', 'dt'].
    """

    # First, get a flat layer
    out: DataFrame = flat_layer(dts, height, height_std, sky_cov_frac)

    # And add to it a sinusoidal fluctuations. Note that nan should stay nan.
    out.loc[:, 'height'] = out.loc[:, 'height'] + \
        np.sin(-np.pi/2 + out['dt']/period*2*np.pi) * amplitude

    return out


def mock_layers(n_ceilos: int, lookback_time: float, hit_gap: float, layer_prms: list) -> DataFrame:
    """ Generate a mock set of cloud layers for a specified number of ceilometers.

    Args:
        n_ceilos (int): number of ceilometers to simulate.
        lookback_time (float): length of the time interval, in s.
        hit_gap (float): number of seconds between ceilometer measurements.
        layer_prms (list of dict): list of layer parameters, provided as a dict for each layer.
            Each dict should specify all the parameters required to generate a
            :py:func:`.sin_layer` (with the exception of ``dts`` that will be computed directly
            from ``lookback_time`` and ``hit_gap``):
            ::

                {'height':1000, 'height_std': 100, 'sky_cov_frac': 1,
                'period': 100, 'amplitude': 0}

    Returns:
        :py:class:`pandas.DataFrame`: a pandas DataFrame with the mock data, ready to be fed to
        ampycloud. Columns ['ceilo', 'dt', 'height', 'type'] correspond to 1) ceilo names, 2) time
        deltas in s, 3) hit heights in ft aal, and 4) hit type.

    TODO:
        - add the possibility to set some VV hits in the mix
        - all of this could be done much more professionally with classes ...

    """

    # A sanity check of the input type, since it is a bit convoluted.
    if not isinstance(layer_prms, list):
        raise AmpycloudError(f'layer_prms should be a list, not: {type(layer_prms)}')
    for (ind, item) in enumerate(layer_prms):
        if not isinstance(item, dict):
            raise AmpycloudError(f'Element {ind} from layer_prms should be a dict,' +
                                 f' not: {type(item)}')
        if not all(key in item.keys() for key in ['height', 'height_std', 'sky_cov_frac',
                                                  'period', 'amplitude']):
            raise AmpycloudError('One or more of the following dict keys are missing in ' +
                                 f"layer_prms[{ind}]: 'height', 'height_std', 'sky_cov_frac'," +
                                 "'period', 'amplitude'.")

    # Let's create the layers individually for each ceilometer
    ceilos = []
    for ceilo in range(n_ceilos):

        # Let's compute the time steps
        n_pts = int(np.ceil(lookback_time/hit_gap))
        dts = np.random.random(n_pts) * -lookback_time

        # Let's now loop through each cloud layer and generate them
        layers: list[DataFrame] = [sin_layer(dts=dts, **prms) for prms in layer_prms]

        # Merge them all into one DataFrame ...
        merged_layers: DataFrame = pd.concat(layers).reset_index(drop=True)
        # Add the type column while I'm at it. Set it to None for now.
        merged_layers['type'] = None

        # Here, adjust the types so that it ranks lowest to highest for every dt step.
        # This needs to be done on a point by point basis, given that layers can cross each other.
        for dt in np.unique(merged_layers['dt']):
            # Get the hit heights, and sort them from lowest to highest
            heights = merged_layers[merged_layers['dt'] == dt]['height'].sort_values(axis=0)

            # Then deal with the other ones
            for (a, height) in enumerate(heights):

                # Except for the first one, any NaN hit gets dropped
                if a > 0 and np.isnan(height):
                    merged_layers.drop(index=heights.index[a],
                                inplace=True)
                elif np.isnan(height):
                    # A non-detection should be type 0
                    merged_layers.loc[heights.index[a], 'type'] = 0
                else:
                    merged_layers.loc[heights.index[a], 'type'] = a+1

        # Add the ceilo info as an int
        merged_layers['ceilo'] = str(ceilo)

        # And store this for later
        ceilos += [merged_layers]

    # Merge it all
    out: DataFrame = pd.concat(ceilos)
    # Sort the timesteps in order, and reset the index
    out = out.sort_values(['dt', 'height']).reset_index(drop=True)

    # Fix the dtypes
    for (col, tpe) in hardcoded.REQ_DATA_COLS.items():
        out[col] = out[col].astype(tpe)

    return out


def canonical_demo_data() -> DataFrame:
    """ This function creates the canonical ampycloud demonstration dataset, that can be used to
    illustrate the full behavior of the algorithm.

    Returns:
        :py:class:`pandas.DataFrame`: the canonical mock dataset with properly-formatted columns.

    """

    # Create the "famous" mock dataset
    n_ceilos = 4
    lookback_time = 900
    hit_gap = 15

    lyrs = [{'height': 1000, 'height_std': 100, 'sky_cov_frac': 0.1, 'period': 10, 'amplitude': 0},
            {'height': 2000, 'height_std': 100, 'sky_cov_frac': 0.5, 'period': 10, 'amplitude': 0},
            {'height': 5000, 'height_std': 200, 'sky_cov_frac': 1, 'period': 1800,
             'amplitude': 1000},
            ]

    # Reset the random seed, but only do this temporarily, so as to not mess things up for the user.
    with utils.tmp_seed(42):
        # Actually generate the mock data
        out: DataFrame = mock_layers(n_ceilos, lookback_time, hit_gap, lyrs)

    # Add a rogue hit, to illustrate the fact that layers that fall below Theta_0 are not
    # reported in the diagnostic diagram, but remain "counted".
    # To avoid confusing users, we will replace an existing hit: pick one closest to -800s.
    swap_id = (abs(out[(out['ceilo'] == '1')*(out['type'] == 2)]['dt']-800)).argmin()
    out.at[swap_id, 'height'] = 3100.0

    return out
