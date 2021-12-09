"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the BSD-3-Clause license.

SPDX-License-Identifier: BSD-3-Clause

Module contains: core ampycloud routines. All fcts meant to be used by users directly are here.

"""

# Import from Python
import warnings
import logging
from typing import Union
from pathlib import Path
from shutil import copy
from datetime import datetime
import pandas as pd
from ruamel.yaml import YAML

# Import from ampycloud
from .errors import AmpycloudError, AmpycloudWarning
from .logger import log_func_call
from .utils.mocker import mock_layers
from .data import CeiloChunk
from . import dynamic
#from .plots.primary import DiagnosticPlot
#from .plots.utils import set_mplstyle

# Instantiate the module logger
logger = logging.getLogger(__name__)

@log_func_call(logger)
def copy_prm_file(save_loc : str = './', which : str = 'defaults') -> None:
    """ Save a local copy of a specific ampycloud parameter file.

    Args:
        save_loc (str, optional): location to save the YML file to. Defaults to './'.

        which (str, optional): name of thee parameter file to copy. Defaults to 'defaults'.

    """

    # Let's take a look at the path I was given
    save_loc = Path(save_loc)
    # I won't create stuff for the users. ampycloud is not that nice.
    if not save_loc.exists():
        raise AmpycloudError('Ouch ! save_loc does not appear to exist !')
    if not save_loc.is_dir():
        raise AmpycloudError('Ouch ! save_loc does not appear to be a directory !')

    # Next, let's look at all the parameter files available ...
    ref_loc = Path(__file__).resolve().parent / 'prms'
    ref_files = [item.name for item in ref_loc.glob('*.yml')]

    # Log this info, in case users want to know which ones exist.
    logger.info('Available parameter files: %s', ref_files)

    if (fname := f'ampycloud_{which}.yml') not in ref_files:
        raise AmpycloudError('Parameter file not found.')

    if (save_loc / fname).exists():
        raise AmpycloudError(f'File {fname} already exists at save_loc={save_loc}')

    # All looks good, let's copy the file
    copy(ref_loc / fname, save_loc / fname)


@log_func_call(logger)
def set_prms(pth : Union[str, Path]) -> None:
    """ Sets the dynamic=scientific ampycloud parameters from a suitable YML file.

    It is recommended to first get a copy of the default ampycloud parameter file and edit the
    parameters as required, to ensure full compliance. See ampycloud.copy_prm_file() for details.

    Args:
        pth (str|Path): path to a YAML parameter file for ampycloud.

    """

    # Set the yaml loading mode ...
    yaml=YAML(typ='safe')

    if isinstance(pth, str):
        # Be nice and try to convert this to a Path
        pth = Path(pth)

    if not isinstance(pth, Path):
        raise AmpycloudError(f'Ouch ! pth should of type str or pathlib.Path, not {type(pth)}')
    if not pth.exists():
        raise AmpycloudError(f'Ouch ! I cannot find {pth}')
    if not pth.is_file():
        raise AmpycloudError(f'Ouch ! {pth} is not a file !')
    if (suf := pth.suffix) != '.yml':
        warnings.warn(f'Hum ... I was expecting a .yml file, but got {suf} instead.'+
                      ' Are you sure this is ok ?', AmpycloudWarning)

    # Extract all the parameters
    with open(pth) as fil:
        prms = yaml.load(fil)

    # Now, assign the prms
    for key in prms:

        logger.info('Setting %s ...', key)
        logger.debug('... with value: %s', prms[key])

        setattr(dynamic, key, prms[key])

@log_func_call(logger)
def reset_prms() -> None:
    """ Reset the ampycloud dynamic=scientific parameters to their default values. """

    pth = Path(__file__).resolve().parent / 'prms' / 'ampycloud_defaults.yml'

    set_prms(pth)

@log_func_call(logger)
def run(data : pd.DataFrame, geoloc : str = None, ref_dt : str = None) -> CeiloChunk:
    """ Run the ampycloud algorithm on a given dataset.

    All the scientific parameters are set dynamically in ampycloud.dynamic. To change them, take a
    look at ampycloud.set_prms().

    Args:
        data (pd.DataFrame): the data to be processed, as a pandas DataFrame.
        geoloc (str, optional): the name of the geographic location where the data was taken.
            Defaults to None.
        ref_dt (str, optional): reference date and time of the observations, corresponding to
            Delta t = 0. Defaults to None.

    Returns:
        CeiloChunk: the data chunk with all the processing outcome bundled cleanly.

    """

    starttime = datetime.now()
    logger.info('Starting an ampycloud run at %s', starttime)

    # First, let's create an CeiloChunk instance ...
    chunk = CeiloChunk(data, geoloc = geoloc, ref_dt = ref_dt)

    # Here, add vital information to the alt_scaling parameters
    # TODO: this is not necessarily the most elegant, and could be done better.
    # Side note: this is only required for the duplicated axes of the diagnostic plots ...
    # Deal with this when I get to the plots
    #for item in [dynamic.SLICING_PRMS, dynamic.GROUPING_PRMS]:
    #    if item['alt_scale_mode'] == 'minmax':
    #        item['alt_scale_kwargs']['min_val'] = np.nanmin(chunk.data['alt'])
    #        item['alt_scale_kwargs']['max_val'] = np.nanmax(chunk.data['alt'])

    # Go through the ampycloud cascade:
    # Run the slicing ...
    chunk.find_slices()
    # ... then the clustering ...
    chunk.find_groups()
    # ... and the layering.
    chunk.find_layers()

    logger.info('End of the ampycloud run in %.1f s', (datetime.now()-starttime).total_seconds())

    return chunk


@log_func_call(logger)
def synop(data : pd.DataFrame, geoloc : str = None) -> str:
    """ Run the ampycloud algorithm on a dataset and extract a synop report of the cloud layers.

    All the scientific parameters are set dynamically in ampycloud.dynamic. To change them, take a
    look at ampycloud.set_prms().

    Args:
        data (pd.DataFrame): the data to be processed, as a pandas DataFrame.
        geoloc (str, optional): the name of the geographic location where the data was taken.
            Defaults to None.

    Returns:
        str: the synop message.

    """

    # First, run the ampycloud algorithm
    chunk = run(data, geoloc=geoloc)

    # Then, return the synop message
    return chunk.metar_msg(synop=True, which='layers')

@log_func_call(logger)
def metar(data : pd.DataFrame, geoloc : str = None) -> str:
    """ Run the ampycloud algorithm on a dataset and extract a METAR report of the cloud layers.

    All the scientific parameters are set dynamically in ampycloud.dynamic. To change them, take a
    look at ampycloud.set_prms().

    Args:
        data (pd.DataFrame): the data to be processed, as a pandas DataFrame.
        geoloc (str, optional): the name of the geographic location where the data was taken.
            Defaults to None.

    Returns:
        str: the synop message.

    """

    # First, run the ampycloud algorithm
    chunk = run(data, geoloc=geoloc)

    # Then, return the synop message
    return chunk.metar_msg(synop=False, which='layers')

@log_func_call(logger)
def demo() -> tuple:
    """ Run the ampycloud algorithm on a demonstration dataset.

    Returns:
        pd.DataFrame, CeiloChunk: the mock dataset used for the demonstration, and the CeiloChunk
        instance.

    """

    # Create the "famous" mock dataset
    n_ceilos = 4
    lookback_time = 1200
    hit_rate = 30

    lyrs = [{'alt': 1000, 'alt_std': 100, 'lookback_time': lookback_time, 'hit_rate': hit_rate,
             'sky_cov_frac': 0.8, 'period': 10, 'amplitude': 0},
            {'alt': 2000, 'alt_std': 100, 'lookback_time': lookback_time, 'hit_rate': hit_rate,
             'sky_cov_frac': 0.5, 'period': 10, 'amplitude': 0},
            {'alt': 5000, 'alt_std': 300, 'lookback_time': lookback_time, 'hit_rate': hit_rate,
             'sky_cov_frac': 1, 'period': 2400, 'amplitude': 1400},
            {'alt': 5000, 'alt_std': 300, 'lookback_time': lookback_time, 'hit_rate': hit_rate,
             'sky_cov_frac': 1, 'period': 2400, 'amplitude': 1400},
            {'alt': 5100, 'alt_std': 500, 'lookback_time': lookback_time, 'hit_rate': hit_rate,
             'sky_cov_frac': 1, 'period': 10, 'amplitude': 0},
            {'alt': 5100, 'alt_std': 500, 'lookback_time': lookback_time, 'hit_rate': hit_rate,
             'sky_cov_frac': 1, 'period': 10, 'amplitude': 0}
            ]

    # Actually generate the mock data
    mock_data = mock_layers(n_ceilos, lyrs)

    assert isinstance(mock_data, pd.DataFrame)

    # Run the ampycloud algorithm
    chunk =  run(mock_data, geoloc='ampycloud demo', ref_dt = str(datetime.now()))

    return mock_data, chunk
