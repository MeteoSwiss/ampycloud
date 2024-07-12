"""
Copyright (c) 2021-2024 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: class for the diagnostic plots
"""

# Import from Python
import logging
from functools import partial
from copy import deepcopy
from typing import Union
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec, rcParams
from matplotlib.lines import Line2D

# Import from this package
from .. import dynamic, scaler, fluffer
from .hardcoded import WIDTH_TWOCOL, MRKS
from .tools import texify, get_scaling_kwargs
from .. import wmo
from ..data import CeiloChunk
from ..version import VERSION

# Instantiate the module logger
logger = logging.getLogger(__name__)


class DiagnosticPlot:
    """ Class used to create diagnostic plots. """

    def __init__(self, chunk: CeiloChunk) -> None:
        """ The init function.

        Args:
            :py:class:`ampycloud.data.CeiloChunk`: a ceilometer Data Chunk.

        """

        # Assign the chunk to a class variable, so I can use it everywhere ...
        self._chunk = chunk

        # Create the figure and axes
        self.new_fig()

    @staticmethod
    def setup_fig() -> tuple:
        """ Setups a diagnsotic plot figure.

        Returns:
            fig, axs: the matplotlib figure, and the axes stored in a list.

        """

        # Create a figure with the proper dimensions.
        fig = plt.figure(figsize=(WIDTH_TWOCOL, 5.5))

        # Use gridspec for a fine control of the figure area.
        fig_gs = gridspec.GridSpec(1, 5,
                                   height_ratios=[1], width_ratios=[1, 0.12, 0.3, 0.18, 0.18],
                                   left=0.08, right=0.99, bottom=0.15, top=0.75,
                                   wspace=0.0, hspace=0.05)

        # Create the individual axes
        ax0 = fig.add_subplot(fig_gs[0, 0])
        ax1 = fig.add_subplot(fig_gs[0, 2], sharey=ax0)
        ax2 = fig.add_subplot(fig_gs[0, 3], sharey=ax0)
        ax3 = fig.add_subplot(fig_gs[0, 4], sharey=ax0)

        # Hide the axis I never want to see ...
        for ax in [ax1, ax2, ax3]:
            ax.axis('off')

        # Store this for later use
        axs = [ax0, ax1, ax2, ax3]

        # Add the copyright
        fig.text(0.995, 0.01, texify(r'\it\smaller\smaller '+f'Created with ampycloud v{VERSION}'),
                 ha='right', va='bottom', rotation=0)

        return fig, axs

    def new_fig(self) -> None:
        """ Assign the fig attribute. """
        self._fig, self._axs = self.setup_fig()

    def show_hits_only(self, show_ceilos: bool = False) -> None:
        """ Shows the ceilometer hits alone.

        Args:
            show_ceilos (bool, optional): whether to distinguish between the different ceilos,
                or not.

        Important:
            This will clear the plot first !

        """

        # Let's create an array of colors for *every* (sigh) point ...
        symb_clrs = np.array(['#000000'] * len(self._chunk.data))

        # If warranted, adjust the colors as a function of the ceilometer id.
        if show_ceilos:

            # Get a list of ceilo colors from the cycler.
            ceilo_clrs = plt.rcParams['axes.prop_cycle'].by_key()['color']
            # Assign them to each hit
            symb_clrs = np.array([ceilo_clrs[self._chunk.ceilos.index(item) % len(ceilo_clrs)]
                         for item in self._chunk.data['ceilo']])

        # What are the VV hits ?
        is_vv = np.array(self._chunk.data['type'] == -1)

        # I want to draw them with no facecolor ... so create an array of "facecolors"
        fcs = np.array(deepcopy(symb_clrs))
        fcs[is_vv] = 'none'

        # Now let's clear the plotting area
        self._axs[0].clear()

        # Add the points
        self._axs[0].scatter(self._chunk.data['dt'], self._chunk.data['height'],
                             marker='o', s=10, edgecolor=symb_clrs,
                             facecolor=list(fcs))

        # If warranted, add the legend about VV hits.
        if np.any(is_vv):
            self.add_vv_legend()

        # If warranted, show the legend for the different ceilometers
        if show_ceilos:
            # Create by hand the legend handles
            elmts = [Line2D([0], [0], ls='', marker='o', color=ceilo_clrs[ind],
                            label=texify(item), markersize=10)
                     for (ind, item) in enumerate(self._chunk.ceilos)]

            # And add them to the plot
            self._axs[0].legend(handles=elmts, loc='upper left', bbox_to_anchor=(1, 1),
                                title='Ceilo. names')

    def show_slices(self) -> None:
        """ Show the slice data. """

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
                             self._chunk.data[self._chunk.data['slice_id'] == -1]['height'],
                             marker='s', s=15, facecolor=fcs[self._chunk.data['slice_id'] == -1],
                             edgecolor='k')

        # Add a quick label ...
        self._axs[1].text(0.5, 1, texify(rf'\smaller $\downarrow$ Slices: {self._chunk.n_slices}'),
                          ha='center', va='bottom',
                          transform=self._axs[1].transAxes)

        # Get a list of approved colors
        all_clrs = plt.rcParams['axes.prop_cycle'].by_key()['color']

        # Then loop through each slice
        if self._chunk.n_slices is not None:
            for ind in range(self._chunk.n_slices):

                # Which hits are in the slice ?
                in_slice = np.array(self._chunk.data['slice_id'] ==
                                    self._chunk.slices.at[ind, 'cluster_id'])

                # Create an array of facecolors ... choose them from my set of colors
                base_clr = all_clrs[ind % len(all_clrs)]
                fcs = np.array([base_clr] * len(self._chunk.data))
                fcs[is_vv] = 'none'

                # I can finally show the points ...
                self._axs[0].scatter(self._chunk.data.loc[in_slice, 'dt'],
                                     self._chunk.data.loc[in_slice, 'height'],
                                     marker='o', s=10, c=fcs[in_slice], edgecolor=base_clr)

                # ... and the corresponding LOWESS-fit used to derive their fluffiness
                _, lowess_pts = fluffer.get_fluffiness(
                    self._chunk.data.loc[in_slice, ['dt', 'height']].values, **self._chunk.prms['LOWESS'])
                self._axs[0].plot(lowess_pts[:, 0], lowess_pts[:, 1],
                                  ls='-', lw=1.5, c=base_clr, drawstyle='steps-mid', zorder=0)

                # Let's also plot the overlap area of the slice
                slice_min = self._chunk.slices.loc[ind, 'height_min']
                slice_max = self._chunk.slices.loc[ind, 'height_max']
                thickness = self._chunk.slices.loc[ind, 'thickness']
                height_pad = self._chunk.prms['GROUPING_PRMS']['height_pad_perc']/100

                # Get some fake data spanning the entire data range
                misc = np.linspace(self._chunk.data['dt'].min(skipna=True),
                                   self._chunk.data['dt'].max(skipna=True), 3)
                self._axs[0].fill_between(misc,
                                          np.ones_like(misc) * (slice_min - height_pad * thickness),
                                          np.ones_like(misc) * (slice_max + height_pad * thickness),
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

                # Show the slice METAR text, plus the fluffiness, plus the isolation status
                msg = r'\smaller '
                msg += wmo.okta2symb(
                    self._chunk.slices.iloc[ind]['okta'],
                    use_metsymb=dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] == 'metsymb')
                msg += ' ' + self._chunk.slices.iloc[ind]['code'] + \
                       rf' $f$:{self._chunk.slices.loc[ind, "fluffiness"]:.0f} ft'
                msg += warn
                self._axs[1].text(0.5, self._chunk.slices.loc[ind, 'height_base'],
                                  texify(msg),
                                  va='center', ha='center', color=base_clr,
                                  bbox={'facecolor': 'none', 'edgecolor': base_clr,
                                        'alpha': alpha, 'ls': '--'})

    def show_groups(self, show_points: bool = False) -> None:
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
        if self._chunk.n_groups is not None:
            for ind in range(self._chunk.n_groups):

                if show_points:
                    # Which hits are in the group ?
                    in_group = np.array(self._chunk.data['group_id'] ==
                                        self._chunk.groups.at[ind, 'cluster_id'])

                    # I can finally show the points ...
                    self._axs[0].scatter(self._chunk.data[in_group]['dt'],
                                         self._chunk.data[in_group]['height'],
                                         marker=MRKS[ind % len(MRKS)],
                                         s=40, c='none', edgecolor='gray', lw=1, zorder=10, alpha=0.5)

                # Stop here if that group has 0 okta.
                if self._chunk.groups.iloc[ind]['okta'] == 0:
                    continue

                # Prepare to display the METAR codes for the groups.
                # First, check if it is significant or not.
                if self._chunk.groups.iloc[ind]['significant']:
                    alpha = 1
                else:
                    alpha = 0

                # Then also check if these groups contain multiple sub-layers ...
                symbs = {-1: r'', 1: r'$-$', 2: r'$=$', 3: r'$\equiv$'}
                warn = ' ' + symbs[self._chunk.groups.iloc[ind]['ncomp']]

                # Show the group METAR text
                msg = r'\smaller ' + wmo.okta2symb(
                    self._chunk.groups.iloc[ind]['okta'],
                    use_metsymb=(dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] == 'metsymb')
                ) + ' ' + self._chunk.groups.iloc[ind]['code'] + warn
                self._axs[2].text(0.5, self._chunk.groups.iloc[ind]['height_base'],
                                  texify(msg),
                                  va='center', ha='center', color='gray',
                                  bbox={'facecolor': 'none', 'edgecolor': 'gray',
                                        'alpha': alpha, 'ls': '--'})

    def show_layers(self) -> None:
        """ Show the layer data. """

        # Add a quick labael ...
        self._axs[3].text(0.5, 1, texify(rf'\smaller $\downarrow$ Layers: {self._chunk.n_layers}'),
                          ha='center', va='bottom',
                          transform=self._axs[3].transAxes)

        # Start looping through every layer ...
        if self._chunk.n_layers is not None:
            for ind in range(self._chunk.n_layers):

                # Which hits are in the layer?
                in_layer = np.array(self._chunk.data['layer_id'] ==
                                    self._chunk.layers.at[ind, 'cluster_id'])

                # I can finally show the points ...
                self._axs[0].scatter(self._chunk.data[in_layer]['dt'],
                                     self._chunk.data[in_layer]['height'],
                                     marker=MRKS[ind % len(MRKS)],
                                     s=40, c='none', edgecolor='k', lw=1, zorder=10, alpha=0.5)

                # Draw the line of the layer base
                if self._chunk.layers.iloc[ind]['okta'] == 0:
                    lls = ':'
                else:
                    lls = '--'

                self._axs[0].axhline(self._chunk.layers.iloc[ind]['height_base'], xmax=1, c='k',
                                     lw=1, zorder=0, ls=lls, clip_on=False)

                # Stop here for empty layers
                if self._chunk.layers.iloc[ind]['okta'] == 0:
                    continue

                # Prepare to display the METAR codes for the layer.
                # First, check if it is significant, or not.
                if self._chunk.layers.iloc[ind]['significant']:
                    alpha = 1
                else:
                    alpha = 0

                # Display the actual METAR text
                msg = r'\smaller ' + wmo.okta2symb(
                    self._chunk.layers.iloc[ind]['okta'],
                    use_metsymb=(dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] == 'metsymb')
                ) + ' ' + self._chunk.layers.iloc[ind]['code']
                self._axs[3].text(0.5, self._chunk.layers.iloc[ind]['height_base'],
                                  texify(msg),
                                  va='center', ha='center', color='k',
                                  bbox={'facecolor': 'none', 'edgecolor': 'k', 'alpha': alpha})

    def add_vv_legend(self) -> None:
        """ Adds a legend about the VV hits."""
        msg = r'\smaller $\circ\equiv\mathrm{VV\ hit}$'
        self._axs[0].text(-0.01, 1.35, texify(msg),
                          transform=self._axs[0].transAxes, ha='right', va='top', c='k',
                          bbox={'facecolor': 'w', 'edgecolor': 'k', 'alpha': 1})

    def add_ceilo_count(self) -> None:
        """ Adds the number of ceilometer present in the data. """
        msg = r'\smaller $n_\mathrm{ceilos}$: ' + f'{len(self._chunk.ceilos)}'
        self._axs[0].text(-0.14, -0.14, texify(msg),
                          transform=self._axs[0].transAxes, ha='left')

    def add_max_hits(self) -> None:
        """ Adds the max_hit_per_layer info. """

        msg = r'\smaller max. hits per layer: ' + str(self._chunk.max_hits_per_layer)
        msg += r'$^{'
        msg += f'8:{self._chunk.prms["MAX_HOLES_OKTA8"]}'
        msg += r'}_{'
        msg += f'0:{self._chunk.prms["MAX_HITS_OKTA0"]}'
        msg += r'}$'

        self._axs[0].text(-0.14, -0.21, texify(msg),
                          transform=self._axs[0].transAxes, ha='left')

    def add_geoloc_and_ref_dt(self) -> None:
        """ Adds info about the chunk geoloc and reference date & time."""

        msg = []
        if self._chunk.geoloc is not None:
            msg += [rf'{self._chunk.geoloc}']
        if self._chunk.ref_dt is not None:
            msg += [r'\smaller $\Delta t_{\rm ref}$: ' + f'{self._chunk.ref_dt}']

        if not len(msg) == 0:
            self._axs[2].text(0.5, -0.02, texify(r'\smaller ' + '\n '.join(msg)),
                              transform=self._axs[2].transAxes, ha='center', va='top')

    def add_ref_metar(self, name: Union[str, None], metar: Union[str, None]) -> None:
        """ Display a reference METAR, for example from human observers, different code, etc ...

        Args:
            name (str) : the name of the reference, e.g. 'Human Observers'.
            metar (str): the METAR code.
        """

        if name is not None or metar is not None:
            msg = rf'\smaller \bf {name}: {metar}'

            # Show it if it contains something ...
            self._axs[2].text(0.5, 1.3, texify(msg),
                              transform=self._axs[2].transAxes, color='k', ha='center',
                              # bbox=dict(facecolor='none', edgecolor='k', alpha=1,
                              #          boxstyle='round, pad=0.25')
                              )

    def add_metar(self) -> None:
        """ Display the ampycloud METAR message."""

        # Combine it all in one message
        msg = r'\smaller \bf ampycloud: ' + self._chunk.metar_msg()

        if self._chunk.msa is not None:
            msg += '\n' + rf'\smaller\smaller MSA: {self._chunk.msa} ft aal'

        # Show the msg ...
        self._axs[2].text(0.5, 1.25, texify(msg),
                          transform=self._axs[2].transAxes, color='k', ha='center',
                          va='top',
                          bbox={'facecolor': 'none', 'edgecolor': 'k', 'alpha': 1,
                                'boxstyle': 'round, pad=0.4'})

    def format_primary_axes(self) -> None:
        """ Deals with the main plot axes """

        # Add the axes labels
        self._axs[0].set_xlabel(r'$\Delta t$ [s]', labelpad=10)
        self._axs[0].set_ylabel(r'Height [ft aal]', labelpad=10)

    def format_slice_axes(self) -> None:
        """ Format the duplicate axes related to the slicing part.

        """

        # Here, only proceed if I have actually found some slices !
        if self._chunk.n_slices is not None and self._chunk.n_slices > 0:

            # In order to show secondary_axis, we need to feed the forward/reverse scaling function
            # with the actual ones used in the code. Since these are dependant upon the data,
            # we need to derive them by hand given what was requested by the user.
            (dt_scale_kwargs, dt_descale_kwargs) = \
                get_scaling_kwargs(self._chunk.data['dt'].values,
                                   'shift-and-scale',
                                   {'scale': self._chunk.prms['SLICING_PRMS']['dt_scale']})

            (height_scale_kwargs, height_descale_kwargs) = \
                get_scaling_kwargs(self._chunk.data['height'].values,
                                   self._chunk.prms['SLICING_PRMS']['height_scale_mode'],
                                   self._chunk.prms['SLICING_PRMS']['height_scale_kwargs'])

            # Then add the secondary axis, using partial function to define the back-and-forth
            # conversion functions.
            secax_x = self._axs[0].secondary_xaxis(
                1.06,
                functions=(partial(scaler.apply_scaling, fct='shift-and-scale', **dt_scale_kwargs),
                           partial(scaler.apply_scaling, fct='shift-and-scale', **dt_descale_kwargs)
                           ))

            secax_y = self._axs[0].secondary_yaxis(
                1.03,
                functions=(partial(scaler.apply_scaling,
                                   fct=self._chunk.prms['SLICING_PRMS']['height_scale_mode'],
                                   **height_scale_kwargs),
                           partial(scaler.apply_scaling,
                                   fct=self._chunk.prms['SLICING_PRMS']['height_scale_mode'],
                                   **height_descale_kwargs)))

            # Add the axis labels
            secax_x.set_xlabel(texify(r'\smaller Slicing $\Delta t$'))
            secax_y.set_ylabel(texify(r'\smaller Slicing height'))

            # And reduce the fontsize while we're at it ...
            secax_x.tick_params(axis='x', which='both', labelsize=rcParams['font.size']-2)
            secax_y.tick_params(axis='y', which='both', labelsize=rcParams['font.size']-2)

    def format_group_axes(self) -> None:
        """ Format the duplicate axes related to the grouping part.

        TODO: add secondary axis for the height rescaling as well. See #91.

        """

        # Only proceed if I have found some clusters ...
        if self._chunk.n_groups is not None and self._chunk.n_groups > 0:

            # In order to show secondary_axis, we need to feed the forward/reverse scaling function
            # with the actual ones used in the code. Since these are dependant upon the data,
            # we need to derive them by hand given what was requested by the user.
            (dt_scale_kwargs, dt_descale_kwargs) = \
                get_scaling_kwargs(self._chunk.data['dt'].values,
                                   'shift-and-scale',
                                   {'scale': self._chunk.prms['GROUPING_PRMS']['dt_scale']})

            # Then add the secondary axis, using partial function to define the back-and-forth
            # conversion functions.
            secax_x = self._axs[0].secondary_xaxis(
                1.25,
                functions=(partial(scaler.apply_scaling, fct='shift-and-scale', **dt_scale_kwargs),
                           partial(scaler.apply_scaling, fct='shift-and-scale', **dt_descale_kwargs)
                           ))

            # Add the axis labels
            secax_x.set_xlabel(texify(r'\smaller Grouping $\Delta t$'))

            # And reduce the fontsize while we're at it ...
            secax_x.tick_params(axis='x', which='both', labelsize=rcParams['font.size']-2)

    def save(self, fn_out: str, fmts: Union[list, None] = None) -> None:
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

    def show(self) -> None:
        """ Shows the plot """

        self._fig.show()

    def close_fig(self) -> None:
        """ Close the figure to free the memory.

        If you need to re-create them, start by generating the figure with the `.new_fig()` method.
        """

        plt.close(self._fig.number)
