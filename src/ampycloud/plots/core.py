"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: core plotting routines
"""

# Import from Python
import logging
from typing import Union

# Import from tbhis module
from ..data import CeiloChunk
from ..logger import log_func_call
from .diagnostics import DiagnosticPlot
from .utils import set_mplstyle

# Instantiate the module logger
logger = logging.getLogger(__name__)

@set_mplstyle
@log_func_call(logger)
def raw_data(chunk : CeiloChunk, show_ceilos : bool = False, show : bool = False,
             save_stem : str = None, save_fmts : Union[list, str] = None,
             ref_name : str = None, ref_metar : str = None) -> None:
    """ A function to plot the raw data of a given CeiloChunk, possibly by coloring the hits as a
    function of the ceilometer it originated from.

    Args:
        chunk (CeiloChunk): the CeiloChunk to look at.
        show_ceilos (bool, optional): if True, hits will be colored as a function of the responsible
            ceilometer. Defaults to False.
        show (bool, optional): will show the plot on the screen if True. Defaults to False.
        save_name (str, optional): if set, will save the plot at this location with this name.
        ref_name (str, optional): name of the source of a reference METAR set with ref_metar.
            Defaults to None.
        ref_metar (str, optional): name of a reference METAR acquired by ref_name. Defaults to None.

    """

    # If the user gave me a unique file format, deal with it
    if isinstance(save_fmts, str):
        save_fmts = [save_fmts]

    # Very well, let's start by instantiating a new DiagnosticPlot.
    adp = DiagnosticPlot(chunk)

    # Create a the plot I want
    adp.show_hits_only(show_ceilos=show_ceilos)
    adp.format_primary_axes()
    adp.add_ceilo_count()
    adp.add_geoloc_and_ref_dt()
    adp.add_ref_metar(ref_name, ref_metar)

    # Save it
    adp.save(save_stem, fmts=save_fmts)

@set_mplstyle
@log_func_call(logger)
def layers(chunk : CeiloChunk, show : bool = False,
           save_stem : str = None, save_fmts : Union[list, str] = None,
           ref_name : str = None, ref_metar : str = None) -> None:
    """ A function to create the ampycloud diagnostic plot all the way to the layering step
    (included). THis is the ultimate ampycloud plot that shows it all.

    Args:
        chunk (CeiloChunk): the CeiloChunk to look at.
        show (bool, optional): will show the plot on the screen if True. Defaults to False.
        save_name (str, optional): if set, will save the plot at this location with this name.
        ref_name (str, optional): name of the source of a reference METAR set with ref_metar.
            Defaults to None.
        ref_metar (str, optional): name of a reference METAR acquired by ref_name. Defaults to None.


    """

    # If the user gave me a unique file format, deal with it
    if isinstance(save_fmts, str):
        save_fmts = [save_fmts]

    # Very well, let's start by instantiating a new DiagnosticPlot.
    adp = DiagnosticPlot(chunk)
    adp.show_slices()
    adp.format_primary_axes()
    #adp.format_slice_axes()
    adp.add_ceilo_count()
    adp.add_geoloc_and_ref_dt()
    adp.show_groups(show_points=False)
    #adp.format_group_axes()
    adp.show_layers()
    adp.add_ref_metar(ref_name, ref_metar)
    adp.add_metar(synop=False)

    # Save it
    adp.save(save_stem, fmts=save_fmts)
