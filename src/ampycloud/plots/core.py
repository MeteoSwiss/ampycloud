"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: core plotting routines
"""

# Import from Python
import logging
from typing import Union

# Import from this module
from ..data import CeiloChunk
from ..logger import log_func_call
from .diagnostics import DiagnosticPlot
from .tools import set_mplstyle

# Instantiate the module logger
logger = logging.getLogger(__name__)


@set_mplstyle
@log_func_call(logger)
def diagnostic(chunk: CeiloChunk, upto: str = 'layers',
               show_ceilos: bool = False,
               ref_metar: Union[str, None] = None,
               ref_metar_origin: Union[str, None] = None,
               show: bool = True,
               save_stem: Union[str, None] = None,
               save_fmts: Union[list, str, None] = None) -> None:
    """ A function to create the ampycloud diagnostic plot all the way to the layering step
    (included). This is the ultimate ampycloud plot that shows it all (or not - you choose !).

    Args:
        chunk (CeiloChunk): the CeiloChunk to look at.
        upto (str, optional): up to which algorithm steps to plot. Can be one of
            ['raw_data', 'slices', 'groups', 'layers']. Defaults to 'layers'.
        show_ceilos (bool, optional): if True, hits will be colored as a function of the
            responsible ceilometer. Defaults to False. No effects unless ``upto='raw data'``.
        ref_metar (str, optional): reference METAR message. Defaults to None.
        ref_metar_origin (str, optional): name of the source of the reference METAR set with
            ref_metar. Defaults to None.
        show (bool, optional): will show the plot on the screen if True. Defaults to False.
        save_stem (str, optional): if set, will save the plot with this stem (which can include a
            path as well). Deafults to None.
        save_fmts (list|str, optional): a list of file formats to export the plot to. Defaults to
            None = ['pdf'].


    Example:
    ::

        from datetime import datetime
        import ampycloud
        from ampycloud.utils import mocker
        from ampycloud.plots import diagnostic

        # First create some mock data for the example
        mock_data = mocker.canonical_demo_data()

        # Then run the ampycloud algorithm on it
        chunk = ampycloud.run(mock_data, geoloc='Mock data', ref_dt=datetime.now())

        # Create the full ampycloud diagnostic plot
        diagnostic(chunk, upto='layers', show=True)

    """

    # If the user gave me a unique file format, deal with it
    if isinstance(save_fmts, str):
        save_fmts = [save_fmts]
    if save_fmts is None:
        save_fmts = ['pdf']

    # Very well, let's start by instantiating a new DiagnosticPlot.
    adp = DiagnosticPlot(chunk)
    if upto == 'raw_data':
        adp.show_hits_only(show_ceilos=show_ceilos)
    if upto in ['slices', 'groups', 'layers']:
        adp.show_slices()
        adp.format_slice_axes()
    if upto in ['groups', 'layers']:
        adp.show_groups(show_points=(upto == 'groups'))
        adp.format_group_axes()
    if upto == 'layers':
        adp.show_layers()
        adp.add_metar()

    # And add all the common stuff
    adp.add_ref_metar(ref_metar_origin, ref_metar)
    adp.format_primary_axes()
    adp.add_ceilo_count()
    adp.add_max_hits()
    adp.add_geoloc_and_ref_dt()

    # Save it
    if save_stem is not None:
        adp.save(save_stem, fmts=save_fmts)

    # Show it ?
    if show:
        adp.show()

    # Close the figure to free the memory
    if not show:
        adp.close_fig()
