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
from .utils.mocker import canonical_demo_data
from .data import CeiloChunk
from . import dynamic

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

    Args:
        data (pd.DataFrame): the data to be processed, as a pandas DataFrame.
        geoloc (str, optional): the name of the geographic location where the data was taken.
            Defaults to None.
        ref_dt (str, optional): reference date and time of the observations, corresponding to
            Delta t = 0. Defaults to None.

    Returns:
        CeiloChunk: the data chunk with all the processing outcome bundled cleanly.

    All that is required to run ampycloud is said (properly formatted) dataset. At the moment,
    specifying ``geoloc`` and ``ref_dt`` serves no purpose other than to enhance plots (should they be
    created) at the moment.

    The input ``data`` must be a ``pandas.DataFrame`` with the following column names (types):
    ::

        'ceilo' (str), 'dt' (float), 'alt' (float), 'type' (int)

    The ``ceilo`` columns contains the names/ids of the ceilometers as ``str``.

    The ``dt`` column contains time deltas, in s, between a given ceilometer observation and
    ``ref_dt``.

    The ``alt`` column contains the cloud base hit altitudes reported by the ceilometers, in ft
    above ground.

    The ``type`` column contains integer that are the hit sequence number, if a given ceilometer
    is reporting multiple hits for a given timestep, or ``-1`` if the hit corresponds to a
    vertical visibility observations.

    It is possible to obtain an example of the format from the
    ``ampycloud.utils.mocker.canonical_demo_dataset()`` routine of the package, namely:
    ::

        from ampycloud.utils import mocker
        mock_data = mocker.canonical_demo_dataset()

    Important:
        ampycloud treats vertical visibility hits just like any other hit. Hence, it is up to the
        user to adjust the vertical visibility hit altitude (if they so desire), and/or ignore
        some of them (if they so desire) prior to feeding them to ampycloud.


    All the scientific parameters are set dynamically in ampycloud.dynamic. From within
    a Python session all these parameters can be changed directly. For example,
    to change the plotting style to 'latex', one would do:
    ::

        from ampycloud import dynamic
        dynamic.MPL_STYLE = 'latex'

    Alternatively, all the scientific parameters can also be defined and fed to ampycloud via a YML
    file. See ``ampycloud.set_prms()`` for details.

    Example:

        In the following example, we create the canonical mock dataset from ampycloud, and run
        the algorithm on it:
        ::

            from datetime import datetime
            import ampycloud
            from ampycloud.utils import mocker

            # Generate the canonical demo dataset for ampycloud
            mock_data = mocker.canonical_demo_data()

            # Run the ampycloud algorithm on it
            chunk = ampycloud.run(mock_data, geoloc='Mock data', ref_dt=datetime.now())

            # Get the resulting METAR/SYNOP message
            print(chunk.metar_msg(synop=False))

    """

    starttime = datetime.now()
    logger.info('Starting an ampycloud run at %s', starttime)

    # First, let's create an CeiloChunk instance ...
    chunk = CeiloChunk(data, geoloc = geoloc, ref_dt = ref_dt)

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
def synop(data : pd.DataFrame) -> str:
    """ Runs the ampycloud algorithm on a dataset and extract a synop report of the cloud layers.

    Args:
        data (pd.DataFrame): the data to be processed, as a pandas DataFrame.

    Returns:
        str: the synop message.

    Example:
    ::

        import ampycloud
        from ampycloud.utils import mocker

        # Generate the canonical demo dataset for ampycloud
        mock_data = mocker.canonical_demo_data()

        # Compute the synop message
        msg = ampycloud.synop(mock_data)
        print(msg)

    """

    # First, run the ampycloud algorithm
    chunk = run(data)

    # Then, return the synop message
    return chunk.metar_msg(synop=True, which='layers')

@log_func_call(logger)
def metar(data : pd.DataFrame, msa : Union[int, float] = None) -> str:
    """ Run the ampycloud algorithm on a dataset and extract a METAR report of the cloud layers.

    Args:
        data (pd.DataFrame): the data to be processed, as a pandas DataFrame.
        msa (int|float, optional): Minimum Sector Altitude. If set, layers above it will not be
            reported. Defaults to None.

    Returns:
        str: the metar message.

    Example:
    ::

        import ampycloud
        from ampycloud.utils import mocker

        # Generate the canonical demo dataset for ampycloud
        mock_data = mocker.canonical_demo_data()

        # Compute the METAR message, with Minimnum Sector Altitude of 10'000 ft
        msg = ampycloud.metar(mock_data, msa=1e5)
        print(msg)

    """

    # First, run the ampycloud algorithm
    chunk = run(data)

    # Then, return the synop message
    return chunk.metar_msg(synop=False, msa=msa, which='layers')

@log_func_call(logger)
def demo() -> tuple:
    """ Run the ampycloud algorithm on a demonstration dataset.

    Returns:
        pd.DataFrame, CeiloChunk: the mock dataset used for the demonstration, and the CeiloChunk
        instance.

    """

    mock_data = canonical_demo_data()

    assert isinstance(mock_data, pd.DataFrame)

    # Run the ampycloud algorithm
    chunk =  run(mock_data, geoloc='ampycloud demo', ref_dt = str(datetime.now()))

    return mock_data, chunk
