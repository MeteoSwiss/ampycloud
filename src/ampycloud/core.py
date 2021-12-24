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
from yaconfigobject import Config

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

    Example:
        ::

            import ampycloud
            ampycloud.copy_prm_file(save_loc='.', which='default')

    .. note::

        There is also a high-level entry point that allows users to get a local copy of the
        ampycloud parameter files directly from the command line:
        ::

            ampycloud_copy_prm_file -which=default

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

    if (fname := f'ampycloud_{which}_prms.yml') not in ref_files:
        raise AmpycloudError(f'Parameter file {fname} not found.')

    if (save_loc / fname).exists():
        raise AmpycloudError(f'File {fname} already exists at save_loc={save_loc}')

    # All looks good, let's copy the file
    copy(ref_loc / fname, save_loc / fname)


@log_func_call(logger)
def set_prms(pth : Union[str, Path]) -> None:
    """ Sets the dynamic=scientific ampycloud parameters from a suitable YAML file.

    Args:
        pth (str|Path): path+filename to a YAML parameter file for ampycloud.

    .. note::
        It is recommended to first get a copy of the default ampycloud parameter file using
        ``ampycloud.copy_prm_file()``, and edit its content as required.

        Doing so should ensure full compliance with default structure of ``dynamic.AMPYCLOUD_PRMS``.

    Example:
        ::

            import ampycloud
            ampycloud.copy_prm_file(save_loc='.', which='default')
            ampycloud.set_prms('./ampycloud_default_prms.yml')

    """

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
        logger.info('Opening (user) parameter file: %s', fil)
        user_prms = Config(paths=[str(fil.parent)], name=str(fil.name))

    # Now, assign the prms
    for (key, item) in user_prms.items():
        if not isinstance(item, dict):
            logger.info('Setting %s ...', key)
            logger.debug('... with value: %s', item)
            dynamic.AMPYCLOUD_PRMS.key = item

        else:
            for (subkey, subitem) in item.items():
                logger.info('Setting %s.%s ...', key, subkey)
                logger.debug('... with value: %s', subitem)
                dynamic.AMPYCLOUD_PRMS.key.subkey = subitem


@log_func_call(logger)
def reset_prms() -> None:
    """ Reset the ampycloud dynamic=scientific parameters to their default values.

    Example:
        ::

            import ampycloud
            from ampycloud import dynamic

            # Change a parameter
            dynamic.AMPYCLOUD_PRMS.OKTA_LIM8 = 95
            # Reset them
            ampycloud.reset_prms()
            print('Back to the default value:', dynamic.AMPYCLOUD_PRMS.OKTA_LIM8)

    """

    dynamic.AMPYCLOUD_PRMS = dynamic.get_default_prms()

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

    All that is required to run ampycloud is a properly formatted dataset. At the moment,
    specifying ``geoloc`` and ``ref_dt`` serves no purpose other than to enhance plots (should they
    be created). There is no special requirements for ``geoloc`` and ``ref_dt``: so long as they are
    strings, you can set them to whatever you please.

    The input ``data`` must be a ``pandas.DataFrame`` with the following column names (types):
    ::

        'ceilo' (str), 'dt' (float), 'alt' (float), 'type' (int)

    The ``ceilo`` columns contains the names/ids of the ceilometers as ``str``.

    The ``dt`` column contains time deltas, in s, between a given ceilometer observation and
    ``ref_dt``.

    The ``alt`` column contains the cloud base hit altitudes reported by the ceilometers, in ft
    above ground.

    The ``type`` column contains integer that correspond to the hit *sequence id*. E.g. if a given
    ceilometer is reporting multiple hits for a given timestep (corresponding to a cloud level 1,
    cloud level 2, cloud level 3, etc ...), the ``type`` of these measurements could be ``1``,
    ``2``, ``3``, ... Any data point with a ``type`` of ``-1`` will be flagged in the ampycloud
    plots as a vertical Visibility (VV) hits, **but it will not be treated any differently than any
    other regular hit**.

    It is possible to obtain an example of the required ``data`` format from the
    ``ampycloud.utils.mocker.canonical_demo_dataset()`` routine of the package, like so:
    ::

        from ampycloud.utils import mocker
        mock_data = mocker.canonical_demo_dataset()

    Caution:
        ampycloud treats Vertical Visibility hits just like any other hit. Hence, it is up to the
        user to adjust the Vertical Visibility hit altitude (and/or ignore some of them) prior to
        feeding them to ampycloud.

    Caution:
        ampycloud uses the ``dt`` and ``ceilo`` values to decide if two hits simultaenous, or not.
        It is thus important that the values of ``dt`` be sufficiently precise to distinguish
        between different measurements. Essentially, each *measurement* (which may be comprised of
        several hits) should be associated to a unique ``(ceilo; dt)`` set of values. Failure to do
        so may result in incorrect estimations of the cloud layer densities. See
        ``ampycloud.data.CeiloChunk.max_hits_per_layer`` for more details.


    All the scientific parameters of the algorithm are set dynamically in ampycloud.dynamic.
    From within a Python session all these parameters can be changed directly. For example,
    to change the Minimum Sector Altitude, one would do:
    ::

        from ampycloud import dynamic
        dynamic.AMPYCLOUD_PRMS.MSA = 5000

    Alternatively, all the scientific parameters can also be defined and fed to ampycloud via a YML
    file. See ``ampycloud.set_prms()`` for details.

    The ``ampycloud.data.CeiloChunk`` instance returned by this function contain all the information
    associated to the ampycloud algorithm, inclduing the raw data and slicing/grouping/layering
    info. Its method `.metar_msg()` provides direct access to the resulting METAR-like message.

    Example:

        In the following example, we create the canonical mock dataset of ampycloud, run
        the algorithm on it, and fetch the resulting METAR-like message:
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
    # ... then the grouping ...
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
def metar(data : pd.DataFrame) -> str:
    """ Run the ampycloud algorithm on a dataset and extract a METAR report of the cloud layers.

    Args:
        data (pd.DataFrame): the data to be processed, as a pandas DataFrame.

    Returns:
        str: the metar message.

    Example:
    ::

        import ampycloud
        from ampycloud.utils import mocker

        # Generate the canonical demo dataset for ampycloud
        mock_data = mocker.canonical_demo_data()

        # Compute the METAR message
        msg = ampycloud.metar(mock_data)
        print(msg)

    """

    # First, run the ampycloud algorithm
    chunk = run(data)

    # Then, return the synop message
    return chunk.metar_msg(synop=False, which='layers')

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
