"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: class for the diagnostic plots
"""

# Import from Python
import logging
from typing import Union
from functools import partial
from copy import deepcopy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib import rcParams

# Import from this package
from ..errors import AmpycloudError
from ..scaler import scaling
from .hardcoded import WIDTH_TWOCOL, MRKS
from .utils import texify
from .. import wmo
from ..data import CeiloChunk
from .. import dynamic

# Instantiate the module logger
logger = logging.getLogger(__name__)

class DiagnosticPlot:
    """ Class used to create diagnsotic plots """

    def __init__(self, chunk : CeiloChunk) -> None:
        """ The init function.

        Args:
            chunk (CeiloChunk): A ceilometer Data Chunk.

        """

        # Assign the chunk to a class variable, so I can use it everywhere ...
        self._chunk = chunk

        # Create the figure, with a suitable width.
        self._fig = plt.figure(figsize=(WIDTH_TWOCOL, 5.5))

        # Use gridspec for a fine control of the figure area.
        fig_gs = gridspec.GridSpec(1, 5,
                                   height_ratios=[1], width_ratios=[1, 0.25, 0.18, 0.18, 0.18],
                                   left=0.08, right=0.99, bottom=0.15, top=0.75,
                                   wspace=0.0, hspace=0.05)

        # Create the individual axes
        ax0 = self._fig.add_subplot(fig_gs[0, 0])
        ax1 = self._fig.add_subplot(fig_gs[0, 2], sharey=ax0)
        ax2 = self._fig.add_subplot(fig_gs[0, 3], sharey=ax0)
        ax3 = self._fig.add_subplot(fig_gs[0, 4], sharey=ax0)

        # Hide the axis I never want to see ...
        for ax in [ax1, ax2, ax3]:
            ax.axis('off')

        # Store this for later use
        self._axs = [ax0, ax1, ax2, ax3]

    def show_hits_only(self, show_ceilos : bool = False) -> None:
        """ Shows the ceilometer hits alone.

        Note:
            This will clear the plot first !

        Args:
            show_ceilos (bool, optional): whether to distinguish between the different ceilos,
                or not.
        """

        # Let's create an array of colors for *every* (sigh) point ...
        symb_clrs = np.array(['#000000'] * len(self._chunk.data))

        # If warranted, adjust the colors as a function of the ceilometer id.
        if show_ceilos:

            # Get a list of ceilo colors from the cycler.
            ceilo_clrs = plt.rcParams['axes.prop_cycle'].by_key()['color']
            # Assign them to each hit
            symb_clrs = [ceilo_clrs[self._chunk.ceilos.index(item)%len(ceilo_clrs)]
                         for item in self._chunk.data['ceilo']]

        # What are the VV hits ?
        is_vv = np.array(self._chunk.data['type'] == -1)

        # I want to draw them with no facecolor ... so create an array of "facecolors"
        fcs = np.array(deepcopy(symb_clrs))
        fcs[is_vv] = 'none'

        # Now let's clear the plotting area
        self._axs[0].clear()

        # Add the points
        self._axs[0].scatter(self._chunk.data['dt'], self._chunk.data['alt'],
                             marker='o', s=10, edgecolor=symb_clrs,
                             facecolor=list(fcs))

        # If warranted, add the legend about VV hits.
        if np.any(is_vv):
            self.add_vv_legend()

        # If warranted, show the legend for the different ceilometers
        if show_ceilos:
            # Create by hand the legend handles
            elmts = [Line2D([0], [0], ls='', marker='o', color=ceilo_clrs[ind],
                            label=texify(r'\smaller ' + item.replace('_', ' ')), markersize=10)
                     for (ind, item) in enumerate(self._chunk.ceilos)]

            # And add them to the plot
            self._axs[0].legend(handles=elmts, loc='upper left', bbox_to_anchor=(1, 1),
                                title='Ceilo. names')

    def show_slices(self) -> None:
        """ Show the slices data. """

        # Let's start by cleaning the plotting area
        self._axs[0].clear()

        # Keep track of vv hits
        is_vv = np.array(self._chunk.data['type'] == -1)

        # I want to draw them with no facecolor ... so create an array of "facecolors"
        fcs = np.array(['#000000'] * len(is_vv))
        fcs[is_vv] = 'none'

        # Add a legend for these, if they exist ...
        if np.any(is_vv):
            self.add_vv_legend()

        # First plot anything that is not assigned to a slice
        self._axs[0].scatter(self._chunk.data[self._chunk.data['slice_id'] == -1]['dt'],
                             self._chunk.data[self._chunk.data['slice_id'] == -1]['alt'],
                             marker='s', s=15, facecolor=fcs[self._chunk.data['slice_id'] == -1],
                             edgecolor='k')

        # Add a quick label ...
        self._axs[1].text(0.5, 1, texify(rf'\smaller $\downarrow$ Slices: {self._chunk.n_slices}'),
                          ha='center', va='bottom',
                          transform=self._axs[1].transAxes)


        # Get a list of approved colors
        all_clrs = plt.rcParams['axes.prop_cycle'].by_key()['color']

        # Then loop through each slice
        for ind in range(self._chunk.n_slices):

            # Which hits are in the slice ?
            in_slice = np.array(self._chunk.data['slice_id'] ==
                                self._chunk.slices.at[ind, 'original_id'])

            # Create an array of facecolors ... choose them from my set of colors
            base_clr = all_clrs[ind % len(all_clrs)]
            fcs = np.array([base_clr] * len(self._chunk.data))
            fcs[is_vv] = 'none'

            # I can finally show the points ...
            self._axs[0].scatter(self._chunk.data[in_slice]['dt'],
                                 self._chunk.data[in_slice]['alt'],
                                 marker='o', s=10, c=fcs[in_slice], edgecolor=base_clr)

            # Let's also plot the overlap area of the slice
            slice_mean = self._chunk.slices.loc[ind, 'alt_mean']
            slice_std = self._chunk.slices.loc[ind, 'alt_std']
            overlap = dynamic.GROUPING_PRMS['overlap']

            # Get some fake data spanning the entire data range
            misc = np.arange(np.nanmin(self._chunk.data['dt']),
                             np.nanmax(self._chunk.data['dt']), 1)
            self._axs[0].fill_between(misc,
                                      np.ones_like(misc) * (slice_mean - overlap * slice_std),
                                      np.ones_like(misc) * (slice_mean + overlap * slice_std),
                                      edgecolor='none', alpha=0.1, zorder=0,
                                      facecolor=base_clr)

            # Stop here if that slice has 0 okta.
            if self._chunk.slices.iloc[ind]['okta'] == 0:
                continue

            # Prepare to display the METAR codes for the slices.
            # First, check if it is isolated or not, and significant or not.
            if self._chunk.slices.iloc[ind]['significant']:
                alpha = 1
            else:
                alpha = 0
            if self._chunk.slices.iloc[ind]['isolated'] is False:
                warn = r' $\Bumpeq$'
            else:
                warn = ''

            # Show the slice METAR text
            msg = r'\smaller ' + wmo.okta2symb(self._chunk.slices.iloc[ind]['okta'],
                                               use_metsymb=(dynamic.MPL_STYLE == 'metsymb')) +\
                ' ' + self._chunk.slices.iloc[ind]['code'] + warn
            self._axs[1].text(0.5, self._chunk.slices.iloc[ind]['alt_base'],
                              texify(msg),
                              va='center', ha='center', color=base_clr,
                              bbox=dict(facecolor='none', edgecolor=base_clr, alpha=alpha, ls='--'))

    def show_groups(self, show_points : bool = False) -> None:
        """ Show the group data.

        Args:
            show_points (bool, optional): whether to actually draw the groups, or simply add the
                info about them. Defaults to False.

        """

        # Add a quick label ...
        self._axs[2].text(0.5, 1,
                          texify(rf'\smaller $\downarrow$ Groups: {self._chunk.n_groups}'),
                          ha='center', va='bottom',
                          transform=self._axs[2].transAxes)

        # Loop through each identified group
        for ind in range(self._chunk.n_groups):

            if show_points:
                # Which hits are in the group ?
                in_group = np.array(self._chunk.data['group_id'] ==
                                      self._chunk.groups.at[ind, 'original_id'])

                # I can finally show the points ...
                self._axs[0].scatter(self._chunk.data[in_group]['dt'],
                                     self._chunk.data[in_group]['alt'],
                                     marker=MRKS[ind%len(MRKS)],
                                     s=40, c='none', edgecolor='gray', lw=1, zorder=10, alpha=0.5)

            # Stop here if that group has 0 okta.
            if self._chunk.groups.iloc[ind]['okta'] == 0:
                continue

            # Prepare to display the METAR codes for the groups.
            # First, check if it is significant or not.
            if self._chunk.groups.iloc[ind]['significant']:
                alpha=1
            else:
                alpha=0

            # Then also check if these groups contain multiple sub-layers ...
            symbs = {-1: r'', 1: r'$-$', 2:r'$=$', 3:r'$\equiv$'}
            warn = ' ' + symbs[self._chunk.groups.iloc[ind]['ncomp']]

            # Show the group METAR text
            msg = r'\smaller ' + wmo.okta2symb(self._chunk.groups.iloc[ind]['okta'],
                                               use_metsymb=(dynamic.MPL_STYLE == 'metsymb')) +\
                ' ' + self._chunk.groups.iloc[ind]['code'] + warn
            self._axs[2].text(0.5, self._chunk.groups.iloc[ind]['alt_base'],
                              texify(msg),
                              va='center', ha='center', color='gray',
                              bbox=dict(facecolor='none', edgecolor='gray', alpha=alpha, ls='--'))

    def show_layers(self) -> None:
        """ Show the layer data. """

        # Add a quick labael ...
        self._axs[3].text(0.5, 1, texify(rf'\smaller $\downarrow$ Layers: {self._chunk.n_layers}'),
                          ha='center', va='bottom',
                          transform=self._axs[3].transAxes)

        # Start looping through every layer ...
        for ind in range(self._chunk.n_layers):

            # Which hits are in the layer?
            in_layer = np.array(self._chunk.data['layer_id'] ==
                                self._chunk.layers.at[ind, 'original_id'])

            # I can finally show the points ...
            self._axs[0].scatter(self._chunk.data[in_layer]['dt'],
                                 self._chunk.data[in_layer]['alt'],
                                 marker=MRKS[ind%len(MRKS)],
                                 s=40, c='none', edgecolor='k', lw=1, zorder=10, alpha=0.5)

            # Draw the line of the layer base
            if self._chunk.layers.iloc[ind]['okta'] == 0:
                lls = ':'
            else:
                lls = '--'

            self._axs[0].axhline(self._chunk.layers.iloc[ind]['alt_base'], xmax=1, c='k',
                        lw=1, zorder=0, ls=lls, clip_on=False)

            # Stop here for empty layers
            if self._chunk.layers.iloc[ind]['okta'] == 0:
                continue

            # Prepare to display the METAR codes for the layer.
            # First, check if it is significant, or not.
            if self._chunk.layers.iloc[ind]['significant']:
                alpha=1
            else:
                alpha=0

            # Display the actual METAR text
            msg = r'\smaller ' + wmo.okta2symb(self._chunk.layers.iloc[ind]['okta'],
                                               use_metsymb=(dynamic.MPL_STYLE == 'metsymb')) +\
                    ' ' + self._chunk.layers.iloc[ind]['code']
            self._axs[3].text(0.5, self._chunk.layers.iloc[ind]['alt_base'],
                              texify(msg),
                              va='center', ha='center', color='k',
                              bbox=dict(facecolor='none', edgecolor='k', alpha=alpha))

    def add_vv_legend(self) -> None:
        """ Adds a legend about the VV hits."""
        msg = r'\smaller $\circ\equiv\mathrm{VV\ hit}$'
        self._axs[0].text(0.01, 1.35, texify(msg),
                          transform=self._axs[0].transAxes, ha='right', va='top', c='k',
                          bbox=dict(facecolor='w', edgecolor='k', alpha=1))

    def add_ceilo_count(self) -> None:
        """ Adds the number of ceilometer present in the data. """
        msg = r'\smaller $n_\mathrm{ceilos}$: ' + f'{len(self._chunk.ceilos)}'
        self._axs[0].text(-0.14, -0.14, texify(msg),
                          transform=self._axs[0].transAxes, ha='left')

    def add_max_hits(self) -> None:
        """ Adds the max_hit_per_layer info. """
        msg = r'\smaller max. hits per layer: ' + str(self._chunk.max_hits_per_layer)
        self._axs[0].text(-0.14, -0.21, texify(msg),
                          transform=self._axs[0].transAxes, ha='left')

    def add_geoloc_and_ref_dt(self) -> None:
        """ Adds info about the chunk geoloc and reference date & time."""

        msg = []
        if self._chunk.geoloc is not None:
            msg += [r'{}'.format(self._chunk.geoloc)]
        if self._chunk.ref_dt is not None:
            msg += [r'\smaller $\Delta t=0$: {}'.format(self._chunk.ref_dt)]

        if not len(msg)==0:
            self._axs[2].text(0.5, -0.21, texify(r'\smaller ' + '\n '.join(msg)),
                              transform=self._axs[2].transAxes, ha='center')

    def add_ref_metar(self, name : str, metar : str) -> None:
        """ Display a reference METAR, for example from human observers, different code, etc ...

        Args:
            name (str) : the name of the reference, e.g. 'Human Observers'.
            metar (str): the metar code.
        """

        if name is not None and metar is not None:
            msg = r'\smaller ${\bf %s}$: %s' % (name, metar)

            # Show it if it contains something ...
            self._axs[2].text(0.5, 1.3, texify(msg),
                              transform=self._axs[2].transAxes, color='k', ha='center',
                              #bbox=dict(facecolor='none', edgecolor='k', alpha=1,
                              #          boxstyle='round, pad=0.25')
                              )

    def add_metar(self, synop : bool = False) -> None:
        """ Display the ampycloud METAR/Synop proposal.
        """

        # Combine it all in one message
        msg = r'\smaller $\bf ampycloud$: ' + self._chunk.metar_msg(synop=synop)

        # Show the msg ...
        self._axs[2].text(0.5, 1.2, texify(msg),
                          transform=self._axs[2].transAxes, color='k', ha='center',
                          bbox=dict(facecolor='none', edgecolor='k', alpha=1,
                                    boxstyle='round, pad=0.4'))

    def format_primary_axes(self) -> None:
        """ Deals with the main plot axes """

        # Add the axes labels
        self._axs[0].set_xlabel(r'$\Delta t$ [s]', labelpad=10)
        self._axs[0].set_ylabel(r'Alt. [ft]', labelpad=10)

    def format_slice_axes(self) -> None:
        """ Format the duplicate axes related to the slicing part. """

        # First, get the scaling parameters, and switch them over to a 'descale' mode ...
        de_dt_scale_kwargs = deepcopy(dynamic.SLICING_PRMS['dt_scale_kwargs'])
        de_dt_scale_kwargs['mode'] = 'descale'
        de_alt_scale_kwargs = deepcopy(dynamic.SLICING_PRMS['alt_scale_kwargs'])
        de_alt_scale_kwargs['mode'] = 'descale'

        # Here, I need to add some vital information to the de_alt_scaling parameters
        # Essentially, we need to set min_/max_val items so we can actually "undo" the scaling
        # and generate the appropriate side-axis.
        if dynamic.SLICING_PRMS['alt_scale_mode'] == 'minmax':
            de_alt_scale_kwargs['min_val'] = np.nanmin(self._chunk.data['alt'])
            de_alt_scale_kwargs['max_val'] = np.nanmax(self._chunk.data['alt'])
        if dynamic.SLICING_PRMS['dt_scale_mode'] == 'minmax':
            de_dt_scale_kwargs['min_val'] = np.nanmin(self._chunk.data['dt'])
            de_dt_scale_kwargs['max_val'] = np.nanmax(self._chunk.data['dt'])

        # Here, only proceed if I have actually found some slices !
        if self._chunk.n_slices > 0:
            # Then add the secondary axis, using partial function to define the back-and-forth
            # conversion functions.
            secax_x = self._axs[0].secondary_xaxis(1.06,
                functions=(partial(scaling, fct=dynamic.SLICING_PRMS['dt_scale_mode'],
                                   **dynamic.SLICING_PRMS['dt_scale_kwargs']),
                           partial(scaling, fct=dynamic.SLICING_PRMS['dt_scale_mode'],
                                   **de_dt_scale_kwargs)))

            secax_y = self._axs[0].secondary_yaxis(1.03,
                functions=(partial(scaling, fct=dynamic.SLICING_PRMS['alt_scale_mode'],
                                   **dynamic.SLICING_PRMS['alt_scale_kwargs']),
                           partial(scaling, fct=dynamic.SLICING_PRMS['alt_scale_mode'],
                                   **de_alt_scale_kwargs)))

            # Finally, let's hide the original axes and ticks to avoid "fat" lines ...
            #self._axs[0].spines['top'].set_visible(False)
            #self._axs[0].spines['right'].set_visible(False)
            #self._axs[0].tick_params(axis='both', which='both', top=False, right=False)

            # Add the axis labels
            secax_x.set_xlabel(texify(r'\smaller Slicing $\Delta t$'))
            secax_y.set_ylabel(texify(r'\smaller Slicing Alt.'))

            # And reduce the fontsize while we're at it ...
            secax_x.tick_params(axis='x', which='both', labelsize=rcParams['font.size']-2)
            secax_y.tick_params(axis='y', which='both', labelsize=rcParams['font.size']-2)

    def format_group_axes(self) -> None:
        """ Format the duplicate axes related to the clsutering part. """

        # First, get the scaling parameters, and switch them over to a 'descale' mode ...
        de_dt_scale_kwargs = deepcopy(dynamic.GROUPING_PRMS['dt_scale_kwargs'])
        de_dt_scale_kwargs['mode'] = 'descale'
        de_alt_scale_kwargs = deepcopy(dynamic.GROUPING_PRMS['alt_scale_kwargs'])
        de_alt_scale_kwargs['mode'] = 'descale'

        # Here, I need to add some vital information to the de_alt_scaling parameters
        # Essentially, we need to set min_/max_val items so we can actually "undo" the scaling
        # and generate the appropriate side-axis.
        if dynamic.GROUPING_PRMS['alt_scale_mode'] == 'minmax':
            de_alt_scale_kwargs['min_val'] = np.nanmin(self._chunk.data['alt'])
            de_alt_scale_kwargs['max_val'] = np.nanmax(self._chunk.data['alt'])
        if dynamic.GROUPING_PRMS['dt_scale_mode'] == 'minmax':
            de_dt_scale_kwargs['min_val'] = np.nanmin(self._chunk.data['dt'])
            de_dt_scale_kwargs['max_val'] = np.nanmax(self._chunk.data['dt'])

        # Only proceed if I have found some clusters ...
        if self._chunk.n_groups > 0:

            # Then add the secondary axis, using partial function to define the back-and-forth
            # conversion functions.
            secax_x = self._axs[0].secondary_xaxis(1.25,
                functions=(partial(scaling, fct=dynamic.GROUPING_PRMS['dt_scale_mode'],
                                   **dynamic.GROUPING_PRMS['dt_scale_kwargs']),
                           partial(scaling, fct=dynamic.GROUPING_PRMS['dt_scale_mode'],
                                   **de_dt_scale_kwargs)))

            secax_y = self._axs[0].secondary_yaxis(1.14,
                functions=(partial(scaling, fct=dynamic.GROUPING_PRMS['alt_scale_mode'],
                                   **dynamic.GROUPING_PRMS['alt_scale_kwargs']),
                           partial(scaling, fct=dynamic.GROUPING_PRMS['alt_scale_mode'],
                                   **de_alt_scale_kwargs)))

            # Add the axis labels
            secax_x.set_xlabel(texify(r'\smaller Grouping $\Delta t$'))
            secax_y.set_ylabel(texify(r'\smaller Grouping Alt.'))

            # And reduce the fontsize while we're at it ...
            secax_x.tick_params(axis='x', which='both', labelsize=rcParams['font.size']-2)
            secax_y.tick_params(axis='y', which='both', labelsize=rcParams['font.size']-2)

    def save(self, fn_out : str, fmts : list = None) -> None:
        """ Saves the plot to file.

        Args:
            fn_out (str): file name out.
            fmts (list or str, optional): list of formats to export the plot to.
                Defaults to None == 'pdf'.

        """

        if fmts is None:
            fmts = ['pdf']

        for fmt in fmts:
            self._fig.savefig(f'{fn_out}.{fmt}')

    # TODO: add a closing routine to close the plot and free memory
