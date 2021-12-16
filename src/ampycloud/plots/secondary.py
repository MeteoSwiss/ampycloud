"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: secondary plotting functions
"""

# Import from Python
import logging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Import from this package
from ..logger import log_func_call
from ..scaler import scaling
from .. import dynamic
from .hardcoded import WIDTH_TWOCOL
from .utils import texify, set_mplstyle

# Instantiate the module logger
logger = logging.getLogger(__name__)

@set_mplstyle
@log_func_call(logger)
def scaling_fcts(show: bool = True, save : bool = False) -> None:
    """ Plots the different scaling functions.

    This is a small utility routine to rapdily see the different altitude scaling options used by
    ampycloud.

    For the "step" sclaing plot, the parameters are taken straight from dynamic.GROUPING_PRMS.

    Args:
       show (bool, optional): show the plot, or not. Defaults to True.
       save (bool, optional): save the plot to pdf, or not. Defaults to False.

    """

    logger.info('Plotting style: %s', dynamic.AMPYCLOUD_PRMS.MPL_STYLE)

    # Create the figure, with a suitable width.
    fig = plt.figure(figsize=(WIDTH_TWOCOL, 4.0))

    # Use gridspec for a fine control of the figure area.
    fig_gs = gridspec.GridSpec(1, 3, height_ratios=[1], width_ratios=[1, 1, 1],
                               left=0.09, right=0.96, bottom=0.18, top=0.9,
                               wspace=0.15, hspace=0.05)

    ax1 = fig.add_subplot(fig_gs[0, 0])
    ax2 = fig.add_subplot(fig_gs[0, 1])
    ax3 = fig.add_subplot(fig_gs[0, 2])

    # Plot the different scaling laws
    alts = np.arange(0, 25000, 10)

    # Plot the slicing scale
    ax1.plot(alts, scaling(alts, fct='const', **{'scale':10}), c='k', lw=2)
    ax1.set_title(texify(r'\smaller const'))

    ax2.plot(alts, scaling(alts, fct='minmax'), c='k', lw=2)
    ax2.set_title(texify(r'\smaller minmax'))

    ax3.plot(alts, scaling(alts, fct='step',
        **dynamic.AMPYCLOUD_PRMS.GROUPING_PRMS['alt_scale_kwargs']), c='k', lw=2)
    ax3.set_title(texify(r'\smaller step'))

    for ax in [ax1, ax2, ax3]:
        ax.set_xlabel('Alt. [ft]')

    ax1.set_ylabel('Scaled Atl.')

    if save:
        fn = 'ampycloud_scaling_fcts.pdf'
        plt.savefig(fn)
        logger.info('%s saved to disk.', fn)

    if show:
        plt.show()
    else:
        plt.close()
