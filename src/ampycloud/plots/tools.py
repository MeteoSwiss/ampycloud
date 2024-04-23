"""
Copyright (c) 2021-2023 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: tools for plots
"""

# Import from Python
import logging
from typing import Callable
from functools import wraps
from pathlib import Path
import copy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import yaml

# Import from ampycloud
from ..errors import AmpycloudError
from ..logger import log_func_call
from .. import dynamic, scaler

# Instantiate the module logger
logger = logging.getLogger(__name__)


def style_pth() -> Path:
    """ Returns the Path to the ampycloud plotting styles. """

    return Path(__file__).parent / 'mpl_styles'


def valid_styles() -> list:
    """ Returns the list of valid plotting styles. """

    return [item.stem for item in style_pth().glob('*.mplstyle')]


def set_mplstyle(func: Callable) -> Callable:
    """ Intended to be used as a decorator around plotting functions, to set the plotting style.

    Returns:
        Callable: the decorator.

    By defaults, the ``base`` ampycloud style will be enabled. Motivated users can tweak it further
    by setting the ``MPL_STYLE`` entry of :py:data:`ampycloud.dynamic.AMPYCLOUD_PRMS` to:

        - ``latex``: to enable the use of a system-wide LaTeX engine, and the Computer Modern font.
        - ``metsymb``: to enable the use of a system-wide LaTeX engine, the Computer Modern font,
          and the ``metsymb`` LaTeX package to display proper okta symbols.

    Important:

        The ``metsymb`` LaTeX package is NOT included with ampycloud, and must be installed
        separately. It is available at: https://github.com/MeteoSwiss/metsymb

    Caution:
        Specifying the ``latex`` or ``metsymb`` style requires a working system-wide LaTeX
        installation. In particular, the following LaTeX packages must be installed:

           - ``cmbright``
           - ``amsmath``
           - ``amssymb``
           - ``relsize``
           - ``metsymb`` (only if the ``MPL_STYLE`` entry of
             :py:data:`ampycloud.dynamic.AMPYCLOUD_PRMS` was set to ``'metsymb'``)

    Todo:
        See https://github.com/MeteoSwiss/ampycloud/issues/18

    """

    @wraps(func)  # This black magic is required for Sphinx to still pickup the func docstrings.
    def inner_deco(*args, **kwargs) -> Callable:
        """ The core function, where the magic happens. """

        # Where are all the plotting parameter files ?
        pth = style_pth()

        # First, always extract the 'base' ampycloud plotting parameters
        with open(pth / 'base.mplstyle', encoding='utf-8') as fil:
            logger.debug("Loading the 'base' style")
            prms = yaml.safe_load(fil)

        # What is the plotting style chosen by the user
        spec_style = dynamic.AMPYCLOUD_PRMS['MPL_STYLE']
        # Let's do some sanity checks on the user input.
        # 0) If I was asked to do nothing special, then do nothing special ...
        if spec_style is None or spec_style == 'base':
            pass
        # 2) Else, I need a string or I cry ...
        elif not isinstance(spec_style, str):
            raise AmpycloudError('dynamic.AMPYCLOUD_PRMS["MPL_STYLE"] type unknown:' +
                                 f' {type(spec_style)}')
        # 3) Is that a supported style ?
        elif spec_style not in valid_styles():
            raise AmpycloudError(f'dynamic.AMPYCLOUD_PRMS["MPL_STYLE"] {spec_style}' +
                                 f' unknown. Should be one of {valid_styles()}.')
        # 4) Request seems legit ... let's load the spec_style ...
        else:
            with open(pth / f'{spec_style}.mplstyle', encoding='utf-8') as fil:
                logger.debug('Loading spec_style: %s', spec_style)
                prms.update(yaml.safe_load(fil))

        # Finally, apply the base plotting style
        with plt.style.context(prms):

            out = func(*args, **kwargs)
            return out

    return inner_deco


@log_func_call(logger)
def texify(msg: str) -> str:
    """ Small utility function that TeX-ifies a string to make it LaTeX robust if warranted by the
    current rcParams settings.

    Args:
        msg (str): message to clean-up

    Returns:
        str: the robust string.
    """

    # Are we using some fancy LaTeX ?
    usetex = rcParams['text.usetex']

    # First deal with the cases when a proper LaTeX is being used
    if usetex:
        msg = msg.replace('%', r'\%')

        # Here, I want to clean the underscore, but ONLY outside of math mode.
        msg_splitted = [item.replace('_', r'\_') if ind % 2 == 0 else item
               for (ind, item) in enumerate(msg.split('$'))]
        msg = '$'.join(msg_splitted)
    # Next cleanup any LaTeX-specific stuff ...
    else:
        msg = msg.replace(r'\smaller', '')
        msg = msg.replace(r'\bf', r'')
        msg = msg.replace(r'\it', r'')

    return msg


@log_func_call(logger)
def get_scaling_kwargs(data: np.ndarray, mode: str, kwargs: dict) -> tuple:
    """ Utility function to extract the **actual, deterministic** parameters required to scale the
    data, given a set of user-defined parameters.

    Args:
        data (pd.Series): the data that was originally scaled by the user.
        mode (str): the name of the scaling used by the user. Must be any mode supported by
            :py:func:`ampycloud.scaler.convert_kwargs` (e.g. ``shift-and-scale``, ``minmax-scale``,
            ``step-scale``).
        kwargs (dict): the scaling parameter set by the user.

    Return:
        tuple: (scale_kwargs, descale_kwargs), the two dict with parameters for the forward/backward
        scaling.

    This is a utility function to aid in the drawing of secondary axis that require to derive the
    "reverse scaling function".

    """

    # Let's create a storage dict, and fill it with what I got from the user.
    scale_kwargs = {}
    scale_kwargs.update(kwargs)

    # Then let's also be explicit about the scaling mode
    scale_kwargs['mode'] = 'do'

    # Use the actual scaler routine used to covert "user params" into "scaling params"
    scale_kwargs = scaler.convert_kwargs(data, mode, **kwargs)

    # Now get a copy, change the mode to 'undo', and we're done !
    descale_kwargs = copy.deepcopy(scale_kwargs)
    descale_kwargs['mode'] = 'undo'

    return (scale_kwargs, descale_kwargs)
