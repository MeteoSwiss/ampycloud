"""
Copyright (c) 2021-2024 MeteoSwiss, contributors listed in AUTHORS.

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
from .utils import utils
from .data import CeiloChunk
from . import dynamic

# Instantiate the module logger
logger = logging.getLogger(__name__)


@log_func_call(logger)
def copy_prm_file(save_loc: str = './', which: str = 'defaults') -> None:
    """ Create a local copy of a specific ampycloud parameter file.

    Args:
        save_loc (str, optional): location to save the YML file to. Defaults to './'.
        which (str, optional): name of the parameter file to copy. Defaults to 'defaults'.

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
    given_path = Path(save_loc)
    # I won't create stuff for the users. ampycloud is not that nice.
    if not given_path.exists():
        raise AmpycloudError('save_loc does not appear to exist !')
    if not given_path.is_dir():
        raise AmpycloudError('save_loc does not appear to be a directory !')

    # Next, let's look at all the parameter files available ...
    ref_loc = Path(__file__).resolve().parent / 'prms'
    ref_files = [item.name for item in ref_loc.glob('*.yml')]

    # Log this info, in case users want to know which ones exist.
    logger.info('Available parameter files: %s', ref_files)

    if (fname := f'ampycloud_{which}_prms.yml') not in ref_files:
        raise AmpycloudError(f'Parameter file {fname} not found.')

    if (given_path / fname).exists():
        raise AmpycloudError(f'File {fname} already exists at save_loc={given_path}')

    # All looks good, let's copy the file
    copy(ref_loc / fname, given_path / fname)


@log_func_call(logger)
def set_prms(pth: Union[str, Path]) -> None:
    """ Sets the dynamic=scientific ampycloud parameters from a suitable YAML file.

    Args:
        pth (str|Path): path+filename to a YAML parameter file for ampycloud.

    .. note::
        It is recommended to first get a copy of the default ampycloud parameter file
        using :py:func:`.copy_prm_file`, and edit its content as required.

        Doing so should ensure full compliance with the default structure of
        :py:data:`.dynamic.AMPYCLOUD_PRMS`.

    .. warning::
        This is NOT a thread-safe way of setting parameters. If you plan on running concurrent
        ampycloud evaluations, parameters should be fed directly to :py:func:`.run`.

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
        raise AmpycloudError(f'pth should of type str or pathlib.Path, not {type(pth)}')
    if not pth.exists():
        raise AmpycloudError(f'I cannot find {pth}')
    if not pth.is_file():
        raise AmpycloudError(f'{pth} is not a file !')
    if (suf := pth.suffix) != '.yml':
        warnings.warn(f'Hum ... I was expecting a .yml file, but got {suf} instead.' +
                      ' Are you sure this is ok ?', AmpycloudWarning)

    # Extract all the parameters
    logger.info('Opening (user) parameter file: %s', pth)
    yaml = YAML(typ='safe')
    user_prms = yaml.load(pth)

    # Now, assign the new prms
    dynamic.AMPYCLOUD_PRMS = utils.adjust_nested_dict(dynamic.AMPYCLOUD_PRMS, user_prms)


@log_func_call(logger)
def reset_prms(which: Union[str, list, None] = None) -> None:
    """ Reset the ampycloud dynamic=scientific parameters to their default values.

    Args:
        which (str|list, optional): (list of) names of parameters to reset specifically.
            If not set (by default), all parameters will be reset.

    Example:
        ::

            import ampycloud
            from ampycloud import dynamic

            # Change a parameter
            dynamic.AMPYCLOUD_PRMS['MAX_HOLES_OKTA8'] = 0
            # Reset them
            ampycloud.reset_prms()
            print('Back to the default value:', dynamic.AMPYCLOUD_PRMS['MAX_HOLES_OKTA8'])

    """

    if which is None:
        dynamic.AMPYCLOUD_PRMS = dynamic.get_default_prms()
        return

    # Ok, reset the parameters one at a time
    default_prms = dynamic.get_default_prms()

    # Clean up which
    which = [which] if isinstance(which, str) else which

    for prm in which:
        if prm not in default_prms.keys():
            raise AmpycloudError(f'Unknown parameter name: {prm}')

        dynamic.AMPYCLOUD_PRMS[prm] = default_prms[prm]


@log_func_call(logger)
def run(data: pd.DataFrame, prms: Union[dict, None] = None, geoloc: Union[str, None] = None,
        ref_dt: Union[str, datetime, None] = None) -> CeiloChunk:
    """ Runs the ampycloud algorithm on a given dataset.

    Args:
        data (pd.DataFrame): the data to be processed, as a :py:class:`pandas.DataFrame`.
        prms (dict, optional): a (nested) dict of parameters to adjust for this specific run.
            This is meant as a thread-safe way of adjusting parameters for different runs. Any
            unspecified parameter will be taken from :py:data:`dynamic.AMPYCLOUD_PRMS` at init time.
        geoloc (str, optional): the name of the geographic location where the data was taken.
            Defaults to None.
        ref_dt (str|datetime.datetime, optional): reference date and time of the observations,
            corresponding to Delta t = 0. Defaults to None. Note that if a datetime instance
            is specified, it will be turned almost immediately to str via ``str(ref_dt)``.

    Returns:
        :py:class:`.data.CeiloChunk`: the data chunk with all the processing outcome bundled
        cleanly.

    All that is required to run the ampycloud algorithm is a properly
    `formatted dataset <https://meteoswiss.github.io/ampycloud/running.html#the-input-data>`__.
    At the moment, specifying ``geoloc`` and ``ref_dt`` serves no purpose other than to enhance
    plots (should they be created). There is no special requirements for ``geoloc`` and ``ref_dt``:
    as long as they are strings, you can set them to whatever you please.

    .. important ::
        ampycloud treats Vertical Visibility hits no differently than any other hit. Hence, it is up
        to the user to adjust the Vertical Visibility hit height (and/or ignore some of them, for
        example) prior to feeding them to ampycloud, so that it can be used as a cloud hit.

    .. important::
        ampycloud uses the ``dt`` and ``ceilo`` values to decide if two hits are simultaenous, or
        not. It is thus important that the values of ``dt`` be sufficiently precise to distinguish
        between different measurements. Essentially, each *measurement* (which may be comprised of
        several hits) should be associated to a unique ``(ceilo; dt)`` set of values. Failure to do
        so may result in incorrect estimations of the cloud layer densities. See
        :py:attr:`.data.CeiloChunk.max_hits_per_layer` for more details.


    All the scientific parameters of the algorithm are set dynamically in the :py:mod:`.dynamic`
    module. From within a Python session all these parameters can be changed directly. For example,
    to change the Minimum Sector Altitude (to be specified in ft aal), one would do:
    ::

        from ampycloud import dynamic
        dynamic.AMPYCLOUD_PRMS['MSA'] = 5000

    Alternatively, the scientific parameters can also be defined and fed to ampycloud via a YAML
    file. See :py:func:`.set_prms()` for details.

    Caution:
        By default, the function :py:func:`.run` will use the parameter values set in
        :py:data:`dynamic.AMPYCLOUD_PRMS`, which is not thread safe. Users interested to run
        **multiple concurrent ampycloud calculations with distinct sets of parameters within the
        same Python session** are thus urged to feed the required parameters directly to
        :py:func:`.run()` via the ``prms`` keyword argument, which expects a (nested) dictionnary
        with keys compatible with :py:data:`dynamic.AMPYCLOUD_PRMS`.

        Examples:
        ::

            # Define only the parameters that are non-default. To adjust the MSA, use:
            prms = {'MSA': 10000}

            # Or to adjust some other algorithm parameters:
            prms = {'LAYERING_PRMS':{'gmm_kwargs':{'scores': 'BIC'}, 'min_prob': 1.0}}


    The :py:class:`.data.CeiloChunk` instance returned by this function contains all the information
    associated to the ampycloud algorithm, inclduing the raw data and slicing/grouping/layering
    info. Its method :py:meth:`.data.CeiloChunk.metar_msg` provides direct access to the resulting
    METAR-like message. Users that require the height, okta amount, and/or exact sky coverage
    fraction of layers can get them via the :py:attr:`.data.CeiloChunk.layers` class property.

    Example:

        In the following example, we create the canonical mock dataset of ampycloud, run
        the algorithm on it, and fetch the resulting METAR-like message:
        ::

            from datetime import datetime
            import ampycloud
            from ampycloud.utils import mocker

            # Generate the canonical demo dataset for ampycloud
            mock_data = mocker.canonical_demo_data()

            # Run the ampycloud algorithm on it, setting the MSA to 10'000 ft aal.
            chunk = ampycloud.run(mock_data, prms={'MSA':10000},
                                  geoloc='Mock data', ref_dt=datetime.now())

            # Get the resulting METAR message
            print(chunk.metar_msg())

            # Display the full information available for the layers found
            print(chunk.layers)

    """

    starttime = datetime.now()
    logger.info('Starting an ampycloud run at %s', starttime)

    # If the user gave me a datetime, convert this to str before proceeding
    if not isinstance(ref_dt, str) and ref_dt is not None:
        ref_dt = str(ref_dt)

    # First, let's create an CeiloChunk instance ...
    chunk = CeiloChunk(data, prms=prms, geoloc=geoloc, ref_dt=ref_dt)

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
def metar(data: pd.DataFrame) -> str:
    """ Run the ampycloud algorithm on a dataset and extract a METAR report of the cloud layers.

    Args:
        data (pd.DataFrame): the data to be processed, as a :py:class:`pandas.DataFrame`.

    Returns:
        str: the METAR-like message.

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

    # Then, return the METAR message
    return chunk.metar_msg(which='layers')


@log_func_call(logger)
def demo() -> tuple:
    """ Run the ampycloud algorithm on a demonstration dataset.

    Returns:
        :py:class:`pandas.DataFrame`, :py:class:`.data.CeiloChunk`: the mock dataset used for the
        demonstration, and the :py:class:`.data.CeiloChunk` instance.

    """

    mock_data = canonical_demo_data()

    assert isinstance(mock_data, pd.DataFrame)

    # Run the ampycloud algorithm
    chunk = run(mock_data, geoloc='ampycloud demo', ref_dt=str(datetime.now()))

    return mock_data, chunk
