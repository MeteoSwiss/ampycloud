"""
Copyright (c) 2021-2023 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: data classes
"""

# Import from Python
from typing import Optional, Union
import logging
import copy
from abc import ABC, abstractmethod
import numpy as np
import numpy.typing as npt
import pandas as pd

# Import from this package
from .errors import AmpycloudError
from .logger import log_func_call
from . import scaler, cluster, layer, fluffer
from . import wmo, icao
from . import dynamic, hardcoded
from .utils import utils

# Instantiate the module logger
logger = logging.getLogger(__name__)


class AbstractChunk(ABC):
    """ Abstract parent class for data chunk classes."""

    #: dict: required data columns
    DATA_COLS = copy.deepcopy(hardcoded.REQ_DATA_COLS)

    @abstractmethod
    def __init__(self, data: pd.DataFrame, prms: Optional[dict] = None,
                 geoloc: Optional[str] = None, ref_dt: Optional[str] = None) -> None:
        """ Init routine for abstract class."""

        # before doing anything else, let's set the different algorithm parameters
        self._prms = self._setup_prms(prms)

        # Assign the data using **a deep copy** to avoid messing with the original one.
        self._data = self._cleanup_pdf(copy.deepcopy(data))

        # Name of the geographic location of the observations
        self._geoloc = geoloc
        # Date and time at the reference
        self._ref_dt = ref_dt

    @property
    def msa(self) -> float:
        """ The Minimum Sector Altitude set when initializing this specific instance. """
        return self.prms['MSA']

    @property
    def msa_hit_buffer(self) -> float:
        """ The Minimum Sector Altitude hit buffer set when initializing this specific instance. """
        return self.prms['MSA_HIT_BUFFER']

    @property
    def data(self) -> pd.DataFrame:
        """ The data of the chunk, as a pandas DataFrame. """
        return self._data

    @property
    def geoloc(self) -> Union[str, None]:
        """ The name of the geographic location of the observations. """
        return self._geoloc

    @property
    def ref_dt(self) -> Union[str, None]:
        """ The reference date and time for the data, i.e. Delta t = 0. """
        return self._ref_dt

    @property
    def prms(self) -> dict:
        """ The dictionnary of ampycloud parameters set at the init of this class instance. """
        return self._prms

    @log_func_call(logger)
    def _cleanup_pdf(self, data: pd.DataFrame) -> pd.DataFrame:
        """ Checks the input pandas DataFrame and adjust it as required.

        Args:
            data (pd.DataFrame): the input data.

        """

        # Begin with a thorough inspection of the dataset
        data = utils.check_data_consistency(data, req_cols=self.DATA_COLS)

        # Then also drop any hits that is too high
        if self.msa is not None:
            hit_alt_lim = self.msa + self.msa_hit_buffer
            logger.info('Cropping hits above MSA+buffer: %s ft', str(hit_alt_lim))
            # Type 1 or less hits above the cut threshold get turned to NaNs, to signal a
            # non-detection below the MSA. Also change the hit type to 0 accordingly !
            data.loc[data[(data.alt > hit_alt_lim) & (data.type <= 1)].index, 'type'] = 0
            data.loc[data[(data.alt > hit_alt_lim) & (data.type <= 1)].index, 'alt'] = np.nan
            # Type 2 or more hits get cropped (there should be only 1 non-detection per time-stamp).
            data = data.drop(data[(data.alt > hit_alt_lim) & (data.type > 1)].index)

        return data

    @log_func_call(logger)
    def _setup_prms(self, prms: dict) -> dict:
        """ Setup a full dict of ampycloud prms given a user input, using default prms where
        necessary. """

        # First, get a deep copy of the (current) default prms
        full_prms = copy.deepcopy(dynamic.AMPYCLOUD_PRMS)

        # Adjust the prms as warranted by the user
        if prms is not None:
            full_prms = utils.adjust_nested_dict(full_prms, prms)

        return full_prms


class CeiloChunk(AbstractChunk):
    """Child class for timeseries of Ceilometers hits, referred to as data 'chunks'.

    This class essentially gathers all the data and processing methods under one roof.

    WARNING:
        Some of these methods are actually intended to be used in order ... Some safety mechanisms
        have been put in place to ensure this actually happens, but still ...

        You've been warned.

    """

    @log_func_call(logger)
    def __init__(self, data: pd.DataFrame, prms: Optional[dict] = None,
                 geoloc: Optional[str] = None, ref_dt: Optional[str] = None) -> None:
        """ CeiloChunk init method.

        Args:
            data (pd.DataFrame): the input data. See above for details.
            prms (dict, optional): dictionnary of ampycloud algorithm parameters.
            geoloc (str, optional): name of the geolocation of the observations.
            ref_dt (str, optional): reference date and time of the observations, corresponding to
                Delta t = 0. Defaults to None.

        The input data is required to be a pandas DataFrame with 4 columns described in
        CeiloChunk.DATA_COLS, i.e. :
        ::

            ['ceilo', 'dt', 'alt', 'type']

        Specifically:

            - ``ceilo``: contains names/ids of the ceilometer associated to the measurements,
              **as str**. This is important to derive correct sky coverage percentage when combining
              data from more than 1 ceilometer, in case ceilometers report multiple hits at the
              same time.

            - ``dt``: time delta between the (planned) METAR issuances time and the
              hit time in s, **as float**. This should typically be a negative number (because
              METARs are assembled using *existing=past* ceilometer observations).

            - ``alt``: cloud base hit altitude in ft, **as float**. The cloud base altitude computed
              by the ceilometer.

            - ``type``: cloud hit type, **as int**. A value n>0 indicates that the hit is the n-th
              (from the ground) that was reported by this specific ceilometer for this specific
              timestep. A value of n=-1 indicates that the cloud hit corresponds to a Vertical
              Visibility hit.

        Note:
            For now, geoloc and ref_dt serve no purposes other than improving the diagnostic plots.
            This is also why ref_dt is a str, such that users can specify it however they please.

        """

        # Call the Parent class init
        super().__init__(data, prms=prms, geoloc=geoloc, ref_dt=ref_dt)

        # For now, we have no slices, no groups, and no layers identified
        self._slices = None
        self._groups = None
        self._layers = None

    @log_func_call(logger)
    def data_rescaled(self, dt_mode: Optional[str] = None, alt_mode: Optional[str] = None,
                      dt_kwargs: Optional[dict] = None, alt_kwargs: Optional[dict] = None) -> pd.DataFrame:
        """ Returns a copy of the data, rescaled according to the provided parameters.

        Args:
            dt_mode (str, optional): scaling rule for the time deltas. Defaults to None.
            alt_mode (str, optional): scaling rule for the altitudes. Defaults to None.
            dt_kwargs (dict, optional): dict of arguments to be fed to the chosen dt scaling
                routine. Defaults to None.
            alt_kwargs (dict, optinal): dict of arguments to be fed to the chosen alt scaling
                routine. Defaults to None.

        Returns:
            pd.DataFrame: a copy of the data, rescaled.

        Note:
            The kwargs approach was inspired by the reply from Jonathan Eunice on
            `SO <https://stackoverflow.com/questions/26534134>`_.

        """

        # Deal with the default NoneType
        if dt_kwargs is None:
            dt_kwargs = {}
        if alt_kwargs is None:
            alt_kwargs = {}

        # Make a deep copy of the data, to avoid messing it up
        out = copy.deepcopy(self.data)

        # Deal with the dt first
        out['dt'] = scaler.apply_scaling(out['dt'], dt_mode, **dt_kwargs)

        # Then the altitudes
        out['alt'] = scaler.apply_scaling(out['alt'], alt_mode, **alt_kwargs)

        return out

    @property
    def ceilos(self) -> list:
        """ The list of all ceilometers included in the data chunk.

        Returns:
            list of str: the list of ceilo names.
        """
        return list(np.unique(self.data['ceilo']))

    @property
    def max_hits_per_layer(self) -> int:
        """ The maximum number of ceilometer hits possible for a given layer, given the chunk data.

        Returns:
            int: the max number of ceilometer hit for a layer. Divide by len(self.ceilos) to get
            the **average** max number of hits per ceilometer per layer (remember: not all
            ceilometers may have the same number of timestamps over the chunk time period !).

        This is the total number of **unique** timesteps from all ceilometers considered.

        Note:
            This value assumes that a layer can contain only 1 hit per ceilometer per timestep,
            i.e. 2 simultaneous hits from a given ceilometer can **never** belong to the same cloud
            layer.

        """

        # For each ceilometer, count the number of individual time stamps ...
        out = [len(np.unique(self.data[self.data['ceilo'] == ceilo]['dt']))
               for ceilo in self.ceilos]

        # ... and sum these to get the result I want.
        return int(np.sum(out))

    def _calculate_base_height_for_selection(
            self,
            data_indexer: pd.Series(dtype=bool),
    ) -> float:
        """Calculate the cloud base height for a selection of data.

        Args:
            data_indexer (pd.Series(dtype=bool)): Boolean series with which we
                want to select the data for which we want to calculate the base height.

        Returns:
            float: The base height of the given data selection.

        """
        # Start computing the base altitude
        # First, compute which points should be considered in terms of lookback time
        return utils.calc_base_alt(
            self.data.sort_values('dt').loc[data_indexer]['alt'].values,
            self.prms['BASE_LVL_LOOKBACK_PERC'],
            self.prms['BASE_LVL_ALT_PERC'],
        )


    def _get_min_sep_for_altitude(self, altitude: float) -> float:
        """Get the minimum separation for a given altitude.

        Args:
            altitude (float): The altitude for which we want to know the minimum
                separation

        Returns:
            float: The minimum separation for the given altitude.

        Raises:
            AmpycloudError: If the length of MIN_SEP_LIMS is not one less than
                MIN_SEP_VALS

        """
        if len(self.prms['MIN_SEP_LIMS']) != \
            len(self.prms['MIN_SEP_VALS']) - 1:
                raise AmpycloudError(
                    '"MIN_SEP_LIMS" must have one less item than "MIN_SEP_VALS".'
                    'Got MIN_SEP_LIMS %i and MIN_SEP_VALS %i',
                    (self.prms['MIN_SEP_LIMS'], self.prms['MIN_SEP_VALS'])
                )

        min_sep_val_id = np.searchsorted(self.prms['MIN_SEP_LIMS'],
                                         altitude)
        min_sep = self.prms['MIN_SEP_VALS'][min_sep_val_id]
        logger.info('Alt: %.1f', altitude)
        logger.info('min_sep value: %.1f', min_sep)
        return min_sep

    def _get_cluster_ids(self, which: str) -> npt.ArrayLike:
        """Get the original IDs of slices, groups or layers.

        Args:
            which (str): 'slice', 'group' or 'array'

        Returns:
            The original IDs

        """
         # What are the original sli/gro/lay ids ?
        cids = np.unique(self.data[which[:-1] + '_id'])

        # For the moment, happily ignore anything that was not assigned to a sli-gro-lay
        # WARNING: *if* the chosen clustering approach changes, one may need to start keeping track
        # of hits that do not get assigned to a sli/gro/lay.
        return np.delete(cids, np.where(cids == -1))

    def _setup_sligrolay_pdf(self, which: str = 'slices') -> tuple[pd.DataFrame, npt.ArrayLike]:
        """Setup a data frame for slices, groups or layers and keep track of IDs.

        Args:
            which (str): One of 'slices', 'groups', 'layers'

        Returns:
            pd.DataFrame: A mostly empty data frame to store slices, groups or layers.
            npt.ArrayLike: The values of the original IDs as given by the clustering/ gmm
                algorithms.

        Raises:
            AmpycloudError: If which is not in ['slices', 'groups', 'layers']

        """
        # What values am I interested in ?
        cols = ['n_hits',  # Duplicate-corrected number of hits
                'perc',  # Duplicate-corrected hit percentage (in %)
                'okta',  # Corresponding okta value
                'alt_base',  # Slice/Group/Layer base altitude
                'alt_mean',  # Slice/Group/Layer mean altitude
                'alt_std',  # Slice/Group/Layer altitude std
                'alt_min',  # Slice/Group/Layer min altitude
                'alt_max',  # Slice/Group/Layer max altitude
                'thickness',  # Slice/Group/Layer thickness
                'fluffiness',  # Slice/Group/Layer fluffiness
                'code',  # METAR code
                'significant',  # bool, whether this is a slice/group/layer that should be reported
                'cluster_id',  # Original id of the slice/group/layer set by the clustering algo
                ]

        # We want to raise early if 'which' is unknown.
        if not which in ['slices', 'groups', 'layers']:
            raise AmpycloudError(
                'Trying to initialize a data frame for %s '
                'which is unknown. Keyword arg "which" must be one of'
                '"slices", "groups" or "layers"'
                %which
            )

        # If I am looking at the slices, also keep track of whether they are isolated, or not.
        if which == 'slices':
            cols += ['isolated']

        # If I am looking at the groups, also keep track of how many sub-components they have
        if which == 'groups':
            cols += ['ncomp']

        # How many slices/groups/layers are there ?
        n_ind = getattr(self, f'n_{which}')

        # If we have None sli/gro/lay found, it means that they weren't computed yet.
        # Be unforgiving and raise an error.
        # Note: this is NOT the same as finding 0 sli/gro/lay, in which case n_ind would be 0.
        if n_ind is None:
            raise AmpycloudError(f'No {which} found. Have they been computed ?')

        # Prepare a pandas DataFrame to store all the info
        pdf = pd.DataFrame(index=range(n_ind), columns=cols)

        cluster_ids = self._get_cluster_ids(which)

        for ind, cid in enumerate(cluster_ids):
            if which == 'groups':
                # Here, check if the layering was already done ... in which case one should NOT
                # be metarizing clusters ! This is one of those places where it is assumed that
                # the layering step comes *after* the grouping step.
                if self._layers is not None:
                    raise AmpycloudError(
                        'Layering already done.'
                        ' If you metarize your groups now, you will loose the'
                        ' layering information !'
                    )
                # If all is as expected, then set the number of sub-components to -1 for now, until
                # the layering step decides otherwise (possibly).
                pdf.loc[ind, 'ncomp'] = -1
            # Keep track of the original sli/gro/lay id
            pdf.loc[ind, 'cluster_id'] = cid

        return pdf, cluster_ids

    def _calculate_cloud_amount(
            self, which: str, pdf: pd.DataFrame, cluster_ids: npt.ArrayLike
        ) -> pd.DataFrame:
        """Calculate cloud amount for a given slice, group or layer.

        Args:
            which (str): One of 'slices', 'groups' or 'layers'
            pdf (pd.DataFrame): A data frame with slices/ groups/ layers.
            cluster_ids (npt.ArrayLike): the original IDs of the slices/ groups/
                layers.

        Returns:
            pd.DataFrame: The input data frame with results in the okta column.

        Results are written to the "okta" column of the DF.

        """
        for ind, cid in enumerate(cluster_ids):
            # Which hits are in this sli/gro/lay ?
            in_sligrolay = self.data[which[:-1]+'_id'] == cid
            # Compute the number of hits of this slice/group/layer for each ceilometer,
            # removing any duplicates.
            # I.e. if hit from layers 2 & 3 from ceilo 1 belong to this sli/gro/lay, count them as
            # one hit only.
            # **BUT** if two hits occur at the same time between ceilo 1 and ceilo 2, count them
            # both ! This is to be consistent with the theoretical max hit number per cloud layer,
            # which assume a max of 1 hit/ceilo/time step.
            hits_per_ceilo = [len(np.unique(self.data[in_sligrolay *
                                            (self.data['ceilo'] == ceilo)]['dt']))
                              for ceilo in self.ceilos]
            pdf.iloc[ind, pdf.columns.get_loc('n_hits')] = np.sum(hits_per_ceilo)
            # Transform this into a percentage
            pdf.iloc[ind, pdf.columns.get_loc('perc')] = \
                pdf.iloc[ind, pdf.columns.get_loc('n_hits')]/self.max_hits_per_layer * 100
            # Compute the corresponding okta level, not fogetting to account for possible buffers
            # for the 0 and 8 okta bins.
            if pdf.iloc[ind, pdf.columns.get_loc('n_hits')] <= self.prms['MAX_HITS_OKTA0']:
                pdf.iloc[ind, pdf.columns.get_loc('okta')] = 0
            elif (
                self.max_hits_per_layer - pdf.iloc[ind, pdf.columns.get_loc('n_hits')]
            ) <= self.prms['MAX_HOLES_OKTA8']:
                pdf.iloc[ind, pdf.columns.get_loc('okta')] = 8
            else:
                pdf.iloc[ind, pdf.columns.get_loc('okta')] = \
                    int(wmo.perc2okta(pdf.iloc[ind, pdf.columns.get_loc('perc')])[0])

        return pdf

    def _add_sligrolay_information(
            self,
            which: str,
            pdf: pd.DataFrame,
            cluster_ids: npt.ArrayLike
        ) -> pd.DataFrame:
        """Add statistical properties to slices/ groups/ layers .

        Args:
            which (str): One of "slices", "groups" or "layers".
            pdf (pd.DataFrame): The data frame holding slices/ groups/ layers.
            cluster_ids (npt.ArrayLike): The original ids of the slices/
                groups/ layers.

        Returns:
            pd.DataFrame: with additional results in the columns alt_min,
                alt_mean, alt_max, alt_std, thickness, fluffiness.

        """
        for ind, cid in enumerate(cluster_ids):
            # Which hits are in this sli/gro/lay ?
            in_sligrolay = self.data[which[:-1]+'_id'] == cid
            # Measure the mean altitude and associated std of the layer
            pdf.iloc[ind, pdf.columns.get_loc('alt_mean')] = \
                self.data.loc[in_sligrolay, 'alt'].mean(skipna=True)
            pdf.iloc[ind, pdf.columns.get_loc('alt_std')] = \
                self.data.loc[in_sligrolay, 'alt'].std(skipna=True)
            # Let's also keep track of the min, max, thickness, and fluffiness values
            pdf.iloc[ind, pdf.columns.get_loc('alt_min')] = \
                self.data.loc[in_sligrolay, 'alt'].min(skipna=True)
            pdf.iloc[ind, pdf.columns.get_loc('alt_max')] = \
                self.data.loc[in_sligrolay, 'alt'].max(skipna=True)
            pdf.iloc[ind, pdf.columns.get_loc('thickness')] = \
                pdf.iloc[ind, pdf.columns.get_loc('alt_max')] - \
                pdf.iloc[ind, pdf.columns.get_loc('alt_min')]
            pdf.iloc[ind, pdf.columns.get_loc('fluffiness')], _ = \
                fluffer.get_fluffiness(
                self.data.loc[in_sligrolay, ['dt', 'alt']].values,
                boost=self.prms['GROUPING_PRMS']['fluffiness_boost'],
                **self.prms['LOWESS'])

        return pdf

    def _calculate_sligrolay_base_height(
            self, which: str, pdf: pd.DataFrame, cluster_ids: npt.ArrayLike
        ) -> pd.DataFrame:
        """Calculate base height for all slices/ groups/ layers.

        Args:
            which (str): One of slices/ groups/ layers.
            pdf (pd.DataFrame): DF holding slices/ groups/ layers.
            cluster_ids (npt.ArrayLike): Original IDs of slices/ groups/ layers.

        Returns:
            pd.DataFrame: with calculatio results in columnm alt_base

        """
        for ind, cid in enumerate(cluster_ids):
            # Which hits are in this sli/gro/lay ?
            in_sligrolay = self.data[which[:-1]+'_id'] == cid
            # Compute the base altitude
            pdf.iloc[ind, pdf.columns.get_loc('alt_base')] = self._calculate_base_height_for_selection(
                in_sligrolay,
            )
        return pdf

    @log_func_call(logger)
    def metarize(
        self, which: str = 'slices') -> None:
        """ Assembles a :py:class:`pandas.DataFrame` of slice/group/layer METAR properties of
        interest.

        Args:
            which (str, optional): whether to process 'slices', 'groups', or 'layers'.
                Defaults to 'slices'.

        The :py:class:`pandas.DataFrame` generated by this method is subsequently available via the
        the appropriate class property :py:attr:`.CeiloChunk.slices`, :py:attr:`.CeiloChunk.groups`,
        or :py:attr:`.CeiloChunk.layers`, depending on the value of the argument ``which``.

        The slice/group/layer parameters computed/derived by this method include:

            * ``n_hits (int)``: duplicate-corrected number of hits
            * ``perc (float)``: sky coverage percentage (between 0-100)
            * ``okta (int)``: okta count
            * ``alt_base (float)``: base altitude
            * ``alt_mean (float)``: mean altitude
            * ``alt_std (float)``: altitude standard deviation
            * ``alt_min (float)``: minimum altitude
            * ``alt_max (float)``: maximum altitude
            * ``thickness (float)``: thickness
            * ``fluffiness (float)``: fluffiness (expressed in altitude units, i.e. ft)
            * ``code (str)``: METAR-like code
            * ``significant (bool)``: whether the layer is significant according to the ICAO rules.
              See :py:func:`.icao.significant_cloud` for details.
            * ``cluster_id (int)``: an ampycloud-internal identification number
            * ``isolated (bool)``: isolation status (for slices only)
            * ``ncomp (int)``: the number of subcomponents (for groups only)

        Important:
            The value of ``n_hits`` is corrected for duplicate hits, to ensure a correct estimation
            of the sky coverage fraction. Essentially, two (or more) *simultaneous hits from the
            same ceilometer* are counted as one only. In other words, if a Type ``1`` and ``2`` hits
            **from the same ceilometer, at the same observation time** are included in a given
            slice/group/layer, they are counted as one hit only. This is a direct consequence of the
            fact that clouds have a single base altitude at any given time [*citation needed*].

        Note:
            The metarize function is modularized in private submethods defined above.

        """

        # setup pd.DataFrame to store slices/ groups/ layers
        pdf, cids = self._setup_sligrolay_pdf(which)

        # calculate cloud amount in okta
        pdf = self._calculate_cloud_amount(which, pdf, cids)

        # calculate slice/ group/ layer base altitude
        pdf = self._calculate_sligrolay_base_height(which, pdf, cids)

        # collect some more information, including fluffiness
        pdf = self._add_sligrolay_information(which, pdf, cids)

        # Then loop through all of the layers/ groups/ slices and add METAR codes
        for ind, _ in enumerate(cids):

            pdf.iloc[ind, pdf.columns.get_loc('code')] = \
                wmo.okta2code(pdf.iloc[ind, pdf.columns.get_loc('okta')]) + \
                wmo.alt2code(pdf.iloc[ind, pdf.columns.get_loc('alt_base')])

        # Set the proper column types
        for cname in ['n_hits', 'okta', 'cluster_id']:
            pdf[cname] = pdf[cname].astype(int)
        for cname in ['perc', 'alt_base', 'alt_mean', 'alt_std', 'alt_min', 'alt_max', 'thickness',
                      'fluffiness']:
            pdf[cname] = pdf[cname].astype(float)
        for cname in ['code']:
            pdf[cname] = pdf[cname].astype(str)
        for cname in ['significant']:
            pdf[cname] = pdf[cname].astype(bool)

        if which == 'slices':
            pdf['isolated'] = pdf['isolated'].astype(bool)
        if which == 'groups':
            pdf['ncomp'] = pdf['ncomp'].astype(int)

        # Sort the table as a function of the base altitude of the sli/gro/lay.
        # This is why having the 'cluster_id' info is useful (so I remember which they are).
        pdf.sort_values('alt_base', inplace=True)

        # Reset the index, 'cause I only need the one.
        pdf.reset_index(drop=True, inplace=True)

        # Almost done ... I just need to figure out which levels are significant.
        pdf.loc[:, 'significant'] = icao.significant_cloud(pdf['okta'].to_list())

        # Finally, assign the outcome where it belongs.
        setattr(self, f'_{which}', pdf)

    @log_func_call(logger)
    def find_slices(self) -> None:
        """ Identify general altitude slices in the chunk data. Intended as the first stage towards
        the identification of cloud layers.

        Important:
            The "parameters" of this function are all set in self.prms['SLICING_PRMS'].

        """

        # Get a scaled **copy** of the data to feed the clustering algorithm
        tmp = self.data_rescaled(dt_mode='shift-and-scale',
                                 dt_kwargs={'scale': self.prms['SLICING_PRMS']['dt_scale']},
                                 alt_mode=self.prms['SLICING_PRMS']['alt_scale_mode'],
                                 alt_kwargs=self.prms['SLICING_PRMS']['alt_scale_kwargs'],
                                 )

        # What are the valid points ?
        valids = tmp['alt'].notna()

        # Add a column to the original data to keep track of the slice id.
        # First, set them all to -1 and force the correct dtype. I hate pandas for this ...
        self.data.loc[:, 'slice_id'] = -1
        self.data['slice_id'] = self.data.loc[:, 'slice_id'].astype(int)

        # If I have only 1 valid point ...
        if len(valids[valids]) == 1:
            self.data.loc[valids, ['slice_id']] = 1
        elif len(valids[valids]) > 1:
            # ... run the clustering on them ...
            _, labels = cluster.clusterize(
                tmp[['dt', 'alt']][valids].to_numpy(), algo='agglomerative',
                **{'linkage': 'average', 'metric': 'manhattan',
                   'distance_threshold': self.prms['SLICING_PRMS']['distance_threshold']})

            # ... and set the labels in the original data
            self.data.loc[self.data['alt'].notna(), ['slice_id']] = labels
        else:
            # If I get no valid points, do nothing at all
            pass

        # Finally, let's metarize these slices !
        self.metarize(
            which='slices',
        )

    def _merge_close_groups(self) -> None:
        """Merge groups that are closer than the minimum separation at their
        respective altitudes.

        Algorithm steps:
            1. Calculate preliminary group base altitude
            2. Start from bottom and search for the first two groups that are
            too close.
            3. Merge these groups and recalculate all base altitudes.
            4. Repeat 2. and 3. until all groups are enough separated.

        The reason this is done iteratively is that there can be multiple overlaps.
        In these cases merging two groups often separates their new (combined)
        base altitude far enough from the base altitude of the next layer above.
        Doing the merging all at once would thus lead to unwanted overgrouping.

        Attention: This method only recalculates height, not amount! If you want
        to have the amounts of the merged groups you need to either call the private method
        _calculate_cloud_amount or the public metarize() method.

        """
        # Let's setup a groups df and get the groups base altitude.
        # setup pd.DataFrame to store slices/ groups/ layers
        prelim_groups, cids = self._setup_sligrolay_pdf('groups')
        # calculate bae altitude
        prelim_groups = self._calculate_sligrolay_base_height(
            'groups', prelim_groups, cids
        )
        # Ordering by altitude
        prelim_groups.sort_values('alt_base', inplace=True)
        prelim_groups.reset_index(drop=True, inplace=True)
        #self.metarize('groups')
        #prelim_groups = self.groups

        min_seps_grp = prelim_groups['alt_base'].apply(self._get_min_sep_for_altitude)
        base_alt_diffs = prelim_groups['alt_base'].diff()
        # create a boolean series to select values, fillna is necessary as
        # first entry of diff will be nan
        lt_min_sep_indexer = (base_alt_diffs < min_seps_grp).fillna(False)
        while len(prelim_groups[lt_min_sep_indexer]) > 0:
            # start with the two lowest layers that are too close
            idx = prelim_groups[lt_min_sep_indexer].index[0]
            # set the group id in the ceilo data to id of group below
            # note: diff() assigns the difference of series elements
            # k, k-1 to k in the difference series. that is why we merge groups
            # with indices k and k-1.
            data_idxer = self.data['group_id'] == prelim_groups['cluster_id'].loc[idx]
            self.data.loc[data_idxer, 'group_id'] = prelim_groups['cluster_id'].iloc[idx - 1]
            # drop the group
            prelim_groups.drop(index=idx, inplace=True)
            # resetting because we must not have index gaps in the next iteration
            prelim_groups.reset_index(drop=True, inplace=True)
            # now we recalculate the base alt for the merged supergroup
            data_idxer = self.data['group_id'] == prelim_groups['cluster_id'].iloc[idx - 1]
            prelim_groups.iloc[
                idx - 1, prelim_groups.columns.get_loc('alt_base')
            ] = self._calculate_base_height_for_selection(data_idxer)
            # as this changes base alt, it is possible that we now are closer
            # to another group, so we have to continue iteratively.
            min_seps_grp = prelim_groups['alt_base'].apply(self._get_min_sep_for_altitude)
            base_alt_diffs = prelim_groups['alt_base'].diff()
            lt_min_sep_indexer = (base_alt_diffs < min_seps_grp).fillna(False)

    @log_func_call(logger)
    def find_groups(self) -> None:
        """ Identifies groups of coherent hits accross overlapping slices. Intended as the second
        stage towards the identification of cloud layers.

        Important:
            The "parameters" of this function are all set in self.prms['GROUPING_PRMS'].

        """

        # If slices do not already exists, raise an error
        # This is one of those location where it is expected that groups are found after
        # slices ...
        if self._slices is None:
            raise AmpycloudError('Slicing not yet done. You cannot find groups without ' +
                                 'finding slices first !')

        # First, make sure that we can keep track of the isolation status of slices.
        self._slices['isolated'] = None

        # Prepare to add the group id to the data frame
        self.data.loc[:, 'group_id'] = None

        # Prepare a list of slices that are overlapping with one another.
        slice_bundles = []

        # Loop through every slice
        for ind in range(len(self.slices)):

            # Get the entire row of information for the slice
            row = self.slices.iloc[ind]

            # Let's get ready to measure the slice separation above and below with respect to the
            # other ones.
            alt_pad = self.prms['GROUPING_PRMS']['alt_pad_perc']/100
            m_lim = row['alt_min'] - alt_pad * row['thickness']
            p_lim = row['alt_max'] + alt_pad * row['thickness']

            # For each other slice below and above, figure out if it is overlapping or not
            seps_m = [m_lim < self.slices.iloc[item]['alt_max'] +
                      alt_pad * self.slices.iloc[item]['thickness'] for item in range(ind)]
            seps_p = [p_lim > self.slices.iloc[item]['alt_min'] -
                      alt_pad * self.slices.iloc[item]['thickness']
                      for item in range(ind+1, len(self.slices), 1)]

            # If the slice is isolated, I can stop here and move on ...
            if not np.any(seps_m) and not np.any(seps_p):
                self._slices.at[ind, 'isolated'] = True
                continue

            # If I get to this point, the slice is not isolated ...
            self._slices.at[ind, 'isolated'] = False

            # What slices are connected to this one ? This is the list of indices of all the slices
            # that are overlapping with the one currently under scrutiny.
            close_inds = list(np.arange(0, ind, 1)[seps_m]) + \
                list(np.arange(ind+1, self.n_slices, 1)[seps_p])

            # Let's add this slice to the list of slices it overlaps with ...
            added = False
            # Loop through each existing slice bundle ...
            for (gind, bundle) in enumerate(slice_bundles):
                # Check if any of the current close slice already belongs to it ...
                if not set(bundle).isdisjoint(close_inds):
                    slice_bundles[gind] += [ind]
                    added = True
                    break
            # If I found no matching slice bundle, create a new one ...
            if not added:
                slice_bundles += [[ind]]

        # At this point, I want to run a Agglomerative Clustering with Single Linkage on each
        # bundle of overlapping slices.
        for grp in slice_bundles:

            # Which ceilometer hits belong to this slice bundle ?
            valids = self.data['slice_id'].isin([self.slices.iloc[ind]['cluster_id']
                                                 for ind in grp])

            # Rescale these points in dt and alt prior to running the single-linkage clustering.
            # dt scaling is provided by the user.
            # alt scaling is derived from the smallest fluffiness of the slice bundle.
            grp_alt_scale = self.slices.loc[grp, 'fluffiness'].min(skipna=True)
            logger.debug('Bundle min. fluffiness: %.1f ft', grp_alt_scale)
            # ... and check against the allowed scaling range
            grp_alt_scale = np.max([np.min(self.prms['GROUPING_PRMS']['alt_scale_range']),
                                    grp_alt_scale])
            grp_alt_scale = np.min([np.max(self.prms['GROUPING_PRMS']['alt_scale_range']),
                                    grp_alt_scale])
            logger.debug('Bundle alt. scale: %.1f ft', grp_alt_scale)
            # Ready to trigger the data rescaling
            tmp = self.data_rescaled(dt_mode='shift-and-scale',
                                     dt_kwargs={'scale': self.prms['GROUPING_PRMS']['dt_scale']},
                                     alt_mode='shift-and-scale',
                                     alt_kwargs={'shift': 0, 'scale': grp_alt_scale})

            # What are the valid points ?
            valids = tmp['alt'].notna() * valids

            # Run the clustering
            nlabels, labels = cluster.clusterize(
                tmp[['dt', 'alt']][valids].to_numpy(), algo='agglomerative',
                **{'linkage': 'single', 'metric': 'euclidean', 'distance_threshold': 1})

            # Based on the clustering, assign each element to a group. The group id is the slice_id
            # to which the majority of the identified (clustered) hits belong.
            for c_ind in range(nlabels):
                cids = self.data[valids]['slice_id'][labels == c_ind]
                self.data.loc[cids.index, 'group_id'] = cids.mode()[0]

        # Deal with the points that have not been changed yet (e.g. from isolated slices)
        to_fill = self.data['group_id'].isna()
        self.data.loc[to_fill, 'group_id'] = self.data.loc[to_fill, 'slice_id']

        # Now we need to separate layers if they are closer than the set
        # minimum separation
        self._merge_close_groups()
        #Let's metarize the merged groups
        self.metarize(which='groups')

    @log_func_call(logger)
    def find_layers(self) -> None:
        """ Identifies individual layers from a list of groups, splitting these in 2 or 3
        (if warranted) *significant* cloud sub-layers. Intended as the third stage towards the
        identification of cloud layers.

        Important:
            The "parameters" of this function are set in self.prms['LAYERING_PRMS'].

        """

        # If groups do not already exists, raise an error
        # This is one of those location where it is expected that layers are found after
        # groups ...
        if self._groups is None:
            raise AmpycloudError('Grouping not yet done. You cannot find layers without ' +
                                 'finding groups first !')

        # Get ready to add the layering info to the data
        self.data.loc[:, 'layer_id'] = None

        # Loop through every group, and look for sub-layers in it ...
        for ind in range(len(self.groups)):

            # Let's extract the altitudes of all the hits in this group ...
            gro_alts = self.data.loc[self.data.loc[:, 'group_id'] ==
                                     self._groups.at[ind, 'cluster_id'],
                                     'alt'].to_numpy()

            # Only look for multiple layers if it is worth it ...
            # 1) Layer density is large enough
            cond1 = self.groups.at[ind, 'okta'] < self.prms['LAYERING_PRMS']['min_okta_to_split']
            # 2) I have more than 30 valid points (GMM is unstable below this amount).
            cond2 = len(gro_alts[~np.isnan(gro_alts)]) < 30
            # 3) Not all the altitudes are the same
            cond3 = len(np.unique(gro_alts[~np.isnan(gro_alts)])) == 1
            if cond1 or cond2 or cond3:
                # Add some useful info to the log
                logger.info(
                    'Skipping the layering: <min_okta_to_split [%s] | <30 pts [%s] | 1 value [%s]',
                    cond1, cond2, cond3)
                # Here, set ncomp to -1 to show clearly that I did NOT actually check it ...
                self.groups.at[ind, 'ncomp'] = -1
                continue

            # Reshape the array in anticipation of the GMM routine ...
            gro_alts = gro_alts.reshape(-1, 1)

            # Identify the minimum layer separation given the overall group base altitude
            min_sep = self._get_min_sep_for_altitude(self.groups.at[ind, 'alt_base'])

            # Handle #78: if the data is comprised of only two distinct altitudes, only look for
            # up to 2 Gaussian components. Else, up to 3.
            ncomp_max = np.min([len(np.unique(gro_alts[~np.isnan(gro_alts)])), 3])
            logger.debug('Setting ncomp_max to: %i', ncomp_max)

            # And feed them to a Gaussian Mixture Model to figure out how many components it has ...
            ncomp, sub_layers_id, _ = layer.ncomp_from_gmm(
                gro_alts, ncomp_max=ncomp_max, min_sep=min_sep,
                layer_base_params={
                    'lookback_perc': self.prms['BASE_LVL_LOOKBACK_PERC'],
                    'alt_perc': self.prms['BASE_LVL_ALT_PERC']
                },
                **self.prms['LAYERING_PRMS']['gmm_kwargs'])

            # Add this info to the log
            logger.debug(' Cluster %s has %i components according to GMM.',
                         {self.groups.at[ind, "code"]}, ncomp)

            # Keep track of what I just found ...
            self.groups.at[ind, 'ncomp'] = ncomp

            # If I need to split it, assign suitable layer ids
            if ncomp > 1:
                self.data.loc[self.data.loc[:, 'group_id'] ==
                              self._groups.at[ind, 'cluster_id'], 'layer_id'] = \
                    100+10*ind+sub_layers_id

        # Deal with the points that have not been assigned a layer id yet
        to_fill = self.data['layer_id'].isna()
        self.data.loc[to_fill, 'layer_id'] = self.data.loc[to_fill, 'group_id']

        # Finally, let's metarize these !
        self.metarize(which='layers',)

    @property
    def n_slices(self) -> Union[None, int]:
        """ Returns the number of slices identified in the data.

        Returns:
            int: the number of slices
        """

        if 'slice_id' not in self.data.columns:
            # This happens if the slicing was not executed yet.
            return None

        return len(np.unique(self.data['slice_id'][self.data['slice_id'] >= 0]))

    @property
    def slices(self) -> pd.DataFrame:
        """ Returns a :py:class:`pandas.DataFrame` with information regarding the different slices
        identified by the slicing step. """
        return self._slices

    @property
    def n_groups(self) -> Union[None, int]:
        """ Returns the number of groups identified in the data.

        Returns:
            int: the number of groups
        """

        if 'group_id' not in self.data.columns:
            # This happens if the grouping was not executed yet.
            return None

        return len(np.unique(self.data['group_id'][self.data['group_id'] >= 0]))

    @property
    def groups(self) -> pd.DataFrame:
        """ Returns a :py:class:`pandas.DataFrame` with information regarding the different groups
        identified by the grouping algorithm. """
        return self._groups

    @property
    def n_layers(self) -> Union[None, int]:
        """ Returns the number of layers identified in the data.

        Returns:
            int: the number of layers.
        """

        if 'layer_id' not in self.data.columns:
            # This happens if the layering did not happen yet
            return None

        return len(np.unique(self.data['layer_id'][self.data['layer_id'] >= 0]))

    @property
    def layers(self) -> pd.DataFrame:
        """ Returns a :py:class:`pandas.DataFrame` with information regarding the different layers
        identified by the layering algorithm. """
        return self._layers

    def metar_msg(self, which: str = 'layers') -> str:
        """ Construct a METAR-like message for the identified cloud slices, groups, or layers.

        Args:
            which (str, optional): whether to look at 'slices', 'groups', or 'layers'. Defaults to
                'layers'.

        Returns:
            str: the METAR-like message.

        Important:
            The ICAO's cloud layer selection rules applicable to METARs will be applied to create
            the resulting ``str`` ! See :py:func:`.icao.significant_cloud` for details.

        .. Caution::
            The Minimum Sector Altitude value set when the :py:class:`.CeiloChunk` instance **was
            initialized** will be applied ! If in doubt, the value used by this method is that set
            in the (parent) class attribute :py:attr:`.AbstractChunk.msa`.

        """

        # Deal with the MSA: set it to infinity if None was specified
        if self.msa is None:
            msa_val = np.infty
        else:
            msa_val = self.msa

        # Some sanity checks to begin with
        if (sligrolay := getattr(self, which)) is None:
            raise AmpycloudError(f'No {which} information found. Have they been computed ?')

        # Deal with the 0 layer situation
        if getattr(self, f'n_{which}') == 0:
            return 'NCD'

        # Deal with the situation where layers have been found ...
        msg = sligrolay['code']
        # What layers are significant *AND* below the MSA ?
        report = sligrolay['significant']*(sligrolay['alt_base'] < msa_val)
        msg = sligrolay['code'][report]
        msg = ' '.join(msg.to_list())

        # Here, deal with the situations when all clouds are above the MSA
        if len(msg) == 0:
            return 'NCD'

        return msg
