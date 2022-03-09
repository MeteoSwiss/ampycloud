"""
Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: generic utilities
"""

# Import from Python
import logging
import warnings
import contextlib
import copy
import numpy as np
import pandas as pd

# Import from this package
from ..errors import AmpycloudError, AmpycloudWarning
from ..logger import log_func_call
from .. import hardcoded

# Instantiate the module logger
logger = logging.getLogger(__name__)


@log_func_call(logger)
def check_data_consistency(pdf: pd.DataFrame,
                           req_cols: dict = None) -> pd.DataFrame:
    """ Assesses whether a given :py:class:`pandas.DataFrame` is compatible with the requirements
    of ampycloud.

    Args:
        pdf (pd.DataFrame): the data to check.
        req_cols (dict): A dictionary in which keys correspond to the required columns, and their
            value are the column type. Defaults to None = the ampycloud requirements.

    Returns:
        pd.DataFrame: the data, possibly cleaned-up of superfluous columns, and with corrected
        dtypes.


    This function will raise an :py:class:`ampycloud.errors.AmpycloudError` and/or
    an :py:class:`ampycloud.errors.AmpycloudWarning` if it identifies very bad and/or very weird
    things in ``pdf``.

    Specifically, the input ``pdf`` must be a :py:class:`pandas.DataFrame` with the following
    column names/types (formally defined in :py:data:`ampycloud.hardcoded.REQ_DATA_COLS`):
    ::

        'ceilo'/pd.StringDtype(), 'dt'/float, 'alt'/float, 'type'/int

    The ``ceilo`` column contains the names/ids of the ceilometers as ``pd.StringDtype()``.
    See the pandas
    `documentation <https://pandas.pydata.org/docs/reference/api/pandas.StringDtype.html>`__
    for more info about this type.

    The ``dt`` column contains time deltas, in seconds, between a given ceilometer
    observation and ``ref_dt`` (i.e. ``obs_time-ref_dt``). Ideally, ``ref_dt`` would be the issuing
    time of the METAR message, such that ``dt`` values are negative, with the smallest one
    corresponding to the oldest measurement.

    The ``alt`` column contains the cloud base hit altitudes reported by the ceilometers, in ft
    above ground.

    The ``type`` column contains integers that correspond to the hit *sequence id*. If a given
    ceilometer is reporting multiple hits for a given timestep (corresponding to a cloud level 1,
    cloud level 2, cloud level 3, etc ...), the ``type`` of these measurements would be ``1``,
    ``2``, ``3``, etc ... Any data point with a ``type`` of ``-1`` will be flagged in the ampycloud
    plots as a vertical Visibility (VV) hits, **but it will not be treated any differently than any
    other regular hit**. Type ``0`` corresponds to no (cloud) detection, in which case the
    corresponding hit altitude should be a NaN.

    Important:
        A **non-detection** corresponds to a valid measurement with a ``dt`` value, a ``type 0``,
        and ``NaN`` as the altitude. It should not be confused with a **non-observation**,
        when no data was acquired at all !

    If it all sounds confusing, it is possible to obtain an example of the required data format
    from the :py:func:`.utils.mocker.canonical_demo_data` routine of the package, like so::

        from ampycloud.utils import mocker
        mock_data = mocker.canonical_demo_data()

    As mentionned above, it is also possible to verify if a given :py:class:`pandas.DataFrame` is
    meeting the ampycloud requirements ahead of time via
    :py:func:`ampycloud.utils.utils.check_data_consistency`::

        from ampycloud.utils.utils import check_data_consistency
        checked_pdf = check_data_consistency(pdf)

    This will raise an :py:class:`ampycloud.errors.AmpycloudError` if:

        * ``pdf`` is not a :py:class:`pandas.DataFrame`.
        * ``pdf`` is missing a required column.
        * ``pdf`` has a length of 0.

    In addition, this will raise an :py:class:`ampycloud.errors.AmpycloudWarning` if:

        * any of ``pdf`` column type is not as expected. Note that in this case, the code will try
          to correct the type on the fly.
        * ``pdf`` has any superfluous columns. In this case, the code will drop them automatically.
        * Any hit altitude is negative.
        * Any ``type 0`` hit has a non-NaN altitude.
        * Any ``type 1`` hit has a NaN altitude.
        * Any ``type 2`` hit does not have a coincident ``type 1`` hit.
        * Any ``type 3`` hit does not have a coincident ``type 2`` hit.

    """

    # Begin by making a deep copy of the data to avoid messing with the user stuff
    data = copy.deepcopy(pdf)

    # Deal with the None default value for the columns
    if req_cols is None:
        req_cols = hardcoded.REQ_DATA_COLS

    # First things first, make sure I was fed a pandas DataFrame
    if not isinstance(data, pd.DataFrame):
        raise AmpycloudError('Ouch ! I was expecting data as a pandas DataFrame,' +
                             f' not: {type(data)}')

    # Make sure the dataframe is not empty.
    # Note: an empty dataframe = no measurements. This is NOT the same as "measuring" clear sky
    # conditions, which would result in NaNs.
    # If I have no measurements, I cannot issue a AutoMETAR. It would make no sense.
    if len(data) == 0:
        raise AmpycloudError("Ouch ! len(data) is 0. I can't work with no data !")

    # Check that all the required columns are present in the data, with the correct format
    for (col, type_req) in req_cols.items():
        # If the required column is missing, raise an Exception.
        if col not in data.columns:
            raise AmpycloudError(f'Ouch ! Column {col} is missing from the input data.')
        # If the column has the wrong data type, complain as well.
        if (type_in := data[col].dtype) != type_req:
            warnings.warn(f'Huh ! Column {col} has type {type_in} instead of {type_req}.',
                          AmpycloudWarning)
            logger.warning('Adjusting the dtype of column %s from %s to %s',
                           col, type_in, type_req)
            data[col] = data[col].astype(type_req)

    # Drop any columns that I do not need for processing
    for key in data.columns:
        if key not in req_cols.keys():
            warnings.warn(f'Huh ! Column {key} is not required by ampycloud.',
                          AmpycloudWarning)
            logger.warning('Dropping the superfluous %s column from the input data.', key)
            data.drop((key), axis=1, inplace=True)

    # A brief sanity check of the altitudes. We do not issue Errors, since the code can cope
    # with those elements: we simply raise Warnings.
    msgs = []
    if np.any(data.loc[:, 'alt'].values < 0):
        msgs += ['Huh ! Some hit altitudes are negative ?!']
    if not np.all(np.isnan(data.loc[data.type == 0, 'alt'])):
        msgs += ['Huh ! Some type=0 hits have non-NaNs altitude values ?!']
    if np.any(np.isnan(data.loc[data.type == 1, 'alt'])):
        msgs += ['Huh ! Some type=1 hits have NaNs altitude values ?!']
    if not np.all(np.in1d(data.loc[data.type == 2, 'dt'].values,
                          data.loc[data.type == 1, 'dt'].values)):
        msgs += ['Huh ! Some type=2 hits have no coincident type=1 hits ?!']
    if not np.all(np.in1d(data.loc[data.type == 3, 'dt'].values,
                          data.loc[data.type == 2, 'dt'].values)):
        msgs += ['Huh ! Some type=3 hits have no coincident type=2 hits ?!']

    # Now save all those messages to the log, and raise Warnings as well.
    for msg in msgs:
        warnings.warn(msg, AmpycloudWarning)
        logger.warning(msg)

    # All done
    return data


@contextlib.contextmanager
def tmp_seed(seed: int):
    """ Temporarily reset the :py:func:`numpy.random.seed` value.

    Adapted from the reply of Paul Panzer on `SO <https://stackoverflow.com/questions/49555991/>`__.

    Example:
    ::

        with temp_seed(42):
            np.random.random(1)

    """

    # Add a note in the logs about what is going on
    logger.debug('Setting a temporary np.random.seed with value %i', seed)

    # Get the current seed
    state = np.random.get_state()

    # Reset it with the temporary one
    np.random.seed(seed)

    # Execute stuff, and reset the original seed once all is over.
    try:
        yield
    finally:
        np.random.set_state(state)


@log_func_call(logger)
def adjust_nested_dict(ref_dict: dict, new_dict: dict, lvls: list = None) -> dict:
    """ Update a given (nested) dictionnary given a second (possibly incomplete) one.

    Args:
        ref_dict (dict): reference dict of dict (of dict of dict ...).
        new_dict (dict): values to update as a dict (of dict or dict of dict ...)
        lvls (list of str, optional): names of the keys of the parent nested dict layers, used
            for reporting useful errors. This is used by the function itself when it calls itself.
            There is no need for the user to set this to anything at first. Defaults to None.

    Returns:
        dict: the updated dict (of dict of dict of dict ...)

    Note:
        Inspired from the reply of Alex Martelli and Alex Telon on
        `SO <https://stackoverflow.com/questions/3232943/>`_.

    """

    if lvls is None:
        lvls = []

    for key, item in new_dict.items():
        lvls += [key]
        if key not in ref_dict.keys():
            warnings.warn(f'Key unknown (and thus ignored): {".".join(lvls)}', AmpycloudWarning)
            continue
        if isinstance(item, dict):
            ref_dict[key] = adjust_nested_dict(ref_dict[key], item, lvls=lvls)
        else:
            ref_dict[key] = item

    return ref_dict
