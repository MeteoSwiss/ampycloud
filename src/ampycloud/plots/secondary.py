"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: secondary plotting functions
"""

# Import from Python
from typing import Union
import logging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Import from this package
from ..logger import log_func_call
from ..scaler import apply_scaling
from .. import dynamic
from .hardcoded import WIDTH_TWOCOL
from .tools import texify, set_mplstyle

# Instantiate the module logger
logger = logging.getLogger(__name__)


@set_mplstyle
@log_func_call(logger)
def scaling_fcts(show: bool = True,
                 save_stem: str = None, save_fmts: Union[list, str] = None) -> None:
    """ Plots the different scaling functions.

    Args:
       show (bool, optional): show the plot, or not. Defaults to True.
       save_stem (str, optional): if set, will save the plot with this stem (which can include a
           path as well). Defaults to None.
       save_fmts (list|str, optional): a list of file formats to export the plot to. Defaults to
           None = ['png'].

    This is a small utility routine to rapidly see the different altitude scaling options used by
    ampycloud.

    For the "step" scaling plot, the parameters are taken straight from dynamic.GROUPING_PRMS.

    Example:
    ::

        from ampycloud.plots.secondary import scaling_fcts

        scaling_fcts(show=True, save_stem='ampycloud_scaling_fcts', save_fmts=['pdf'])

    """

    # Create the figure, with a suitable width.
    fig = plt.figure(figsize=(WIDTH_TWOCOL, 4.0))

    # Use gridspec for a fine control of the figure area.
    fig_gs = gridspec.GridSpec(1, 3, height_ratios=[1], width_ratios=[1, 1, 1],
                               left=0.07, right=0.96, bottom=0.18, top=0.9,
                               wspace=0.15, hspace=0.05)

    ax1 = fig.add_subplot(fig_gs[0, 0])
    ax2 = fig.add_subplot(fig_gs[0, 1])
    ax3 = fig.add_subplot(fig_gs[0, 2])

    # Plot the different scaling laws
    alts = np.arange(0, 25000, 10)

    # Plot the slicing scale
    ax1.plot(alts, apply_scaling(alts, fct='shift-and-scale', **{'scale': 1000}), c='k', lw=2)
    ax1.set_title(texify(r'\smaller shift-and-scale'))

    ax2.plot(alts, apply_scaling(alts, fct='minmax-scale'), c='k', lw=2)
    ax2.set_title(texify(r'\smaller minmax-scale'))

    ax3.plot(alts, apply_scaling(
        alts, fct='step-scale',
        **dynamic.AMPYCLOUD_PRMS['GROUPING_PRMS']['alt_scale_kwargs']), c='k', lw=2)
    ax3.set_title(texify(r'\smaller step-scale'))

    for ax in [ax1, ax2, ax3]:
        ax.set_xlabel('x')

    ax1.set_ylabel('Scaled x')

    if save_fmts is None:
        save_fmts = ['png']

    if save_stem is not None:
        for fmt in save_fmts:
            out = f'{save_stem}.{fmt}'
            plt.savefig(out)
            logger.info('%s saved to disk.', out)

    if show:
        plt.show()
    else:
        plt.close()
