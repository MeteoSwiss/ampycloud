"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: tools to create mock datasets
"""

# Import from Python
import logging
from typing import Union
import numpy as np
import pandas as pd

# import from ampycloud
from ..logger import log_func_call
from ..errors import AmpycloudError

logger = logging.getLogger(__name__)

# Define a proper random number generator
np.random.seed(42)

@log_func_call(logger)
def flat_layer(alt : float, alt_std : float, lookback_time : float,
               hit_rate : float, sky_cov_frac : float) -> pd.DataFrame:
    """ Generates a mock, flat, Gaussian cloud layer around a given altitude.

    Args:
        alt (float): layer mean altitude, in ft.
        alt_std (float): layer altitude standard deviation, in ft.
        lookback_time (float): length of the time interval, in s.
        hit_rate (float): rate of data acquisition, in s.
        sky_cov_frac (float): Sky coverage fraction. Random hits will be set to NaN to
            reach this value. Must be 0 <= x <= 1.

    Returns:
        pd.DataFrame: the simulated layer with columns ['alt', 'dt'].
    """

    # How many points do I need to generate ?
    n_pts = int(np.ceil(lookback_time/hit_rate))

    # Create the storage structure
    out = pd.DataFrame(columns=['alt', 'dt'], dtype=float)

    # Generate the random altitude data
    out['alt'] = np.random.normal(loc=alt, scale=alt_std, size=n_pts)
    # Cleanup any negative altitudes, if warranted.
    out.loc[out['alt']<=0, 'alt'] = np.nan
    out['dt'] = np.random.random(n_pts) * -lookback_time

    # Empty hits to get the requested sky coverage fraction
    # First extract the hits I want to keep ...
    to_keep = out.sample(frac=sky_cov_frac)
    # ... then get rid of the alt values everywhere ...
    out['alt'] = np.nan
    # ... and re-set the values I choose to keep.
    out.loc[to_keep.index] = to_keep

    return out

@log_func_call(logger)
def sin_layer(alt : float, alt_std : float, lookback_time : float,
              hit_rate : float, sky_cov_frac : float,
              period : Union[int, float], amplitude : Union[int, float]) -> pd.DataFrame:
    """ Generates a sinusoidal cloud layer.

    Args:
        alt (float): layer mean altitude, in ft.
        alt_std (float): layer altitude standard deviation, in ft.
        lookback_time (float): length of the time interval, in s.
        hit_rate (float): rate of data acquisition.
        sky_cov_frac (float, optional): Sky coverage fraction. Random hits will be set to NaN to
            reach this value. Must be 0 <= x <= 1.
        period (int|float): period of the sine-wave, in s.
        amplitude (int|float): amplitude of the sine-wave, in ft.

    Returns:
        pd.DataFrame: the simulated layer with columns ['alt', 'dt'].
    """

    # First, get a flat layer
    out = flat_layer(alt, alt_std, lookback_time, hit_rate, sky_cov_frac)

    # And add to it a sinusoidal fluctuations. Note that nan should stay nan.
    out['alt'] = out['alt'] + np.sin(-np.pi/2 + out['dt']/period*2*np.pi) * amplitude

    return out


def mock_layers(n_ceilos : int, layer_prms : list) -> pd.DataFrame:
    """ Generate a mock set of cloud layers for a specified number of ceilometers.

    TODO:
        - add the possibility to set some VV hits in the mix
        - add the possibility to have multiple hits at the same time steps
        - all of this could be done much more professionally with classes ...

    Args:
        n_ceilos (int): number of ceilometers to simulate.
        layer_prms (list of dict): list of layer parameters, provided as a dict for each layer.
            Each dict should specify all the parameters required to generate a sin layer, e.g.:
            ::

                {'alt':1000, 'alt_std': 100, 'lookback_time' : 1200,
                'hit_rate': 60, 'sky_cov_frac': 1,
                'period': 100, 'amplitude': 0}


    Returns:
        DataFrame: a pandas DataFrame with the mock data, ready to be fed to ampycloud. Columns
        ['ceilo', 'dt', 'alt', 'type'] correspond to 1) ceilo names, 2) time deltas in s,
        3) hit altitudes in ft, and 4) hit type.

    """

    # A simple sanity check of the input type, since it is a bit convoluted.
    if not isinstance(layer_prms, list):
        raise AmpycloudError(f'Ouch ! layer_prms should be a list, not: {type(layer_prms)}')

    for (ind, item) in enumerate(layer_prms):
        if not isinstance(item, dict):
            raise AmpycloudError(f'Ouch ! Element {ind} from layer_prms should be a dict,' +
                                  f' not: {type(item)}')
        if not all(key in item.keys() for key in ['alt', 'alt_std', 'lookback_time', 'hit_rate',
                                                  'period', 'amplitude']):
            raise AmpycloudError('Ouch ! One or more of the following dict keys are missing in '+
                                 f"layer_prms[{ind}]: 'alt', 'alt_std', 'lookback_time',"+
                                 "'hit_rate','period', 'amplitude'.")

    # Let's create the layers individually for eahc ceilometer
    ceilos = []
    for ceilo in range(n_ceilos):

        # Let's now lopp through each cloud layer and generate them
        layers = [sin_layer(**prms) for prms in layer_prms]

        # Merge them all into one ...
        layers = pd.concat(layers).reset_index(drop=True)

        # Add the type column
        layers['type'] = 99

        # Add the ceilo info as an int
        layers['ceilo'] = str(ceilo)

        # And store this for later
        ceilos += [layers]

    # Merge it all
    out = pd.concat(ceilos)
    # Sort the timesteps in order, and reset the index
    out = out.sort_values('dt').reset_index(drop=True)

    # Fix the dtypes
    out['dt'] = out['dt'].astype(float)
    out['alt'] = out['alt'].astype(float)
    out['type'] = out['type'].astype(int)
    out['ceilo'] = out['ceilo'].astype(str)

    return out
