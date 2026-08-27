"""
Copyright (c) 2021-2026 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: the metarization logic for CeiloChunk, i.e. turning slices/groups/layers into
METAR-like sky coverage information.
"""

# Import from Python
import logging
import warnings
from typing import TYPE_CHECKING, Optional
import numpy as np
import pandas as pd

# Import from this package
from .errors import AmpycloudError, AmpycloudWarning
from .logger import log_func_call
from . import wmo, icao, fluffer

# Instantiate the module logger
logger = logging.getLogger(__name__)


class MetarizeMixin:
    """Mixin gathering the CeiloChunk methods in charge of turning slices/groups/layers into
    METAR-like sky coverage information."""

    if TYPE_CHECKING:
        # Attributes/methods expected from the class. Read-only attributes are declared as properties to match
        # the property definitions found in AbstractChunk/CeiloChunk.
        @property
        def data(self) -> pd.DataFrame: ...

        @property
        def prms(self) -> dict: ...

        @property
        def msa(self) -> Optional[float]: ...

        @property
        def ceilos(self) -> list: ...

        @property
        def max_hits_per_layer(self) -> int: ...

        _layers: Optional[pd.DataFrame]
        _clouds_above_msa_buffer: bool

    def _get_cluster_ids(self, which: str) -> np.ndarray:
        """Get the original IDs of slices, groups or layers.

        Args:
            which (str): 'slice', 'group' or 'array'

        Returns:
            The original IDs

        """
        # What are the original sli/gro/lay ids ?
        cids = np.unique(self.data[which[:-1] + "_id"])

        # For the moment, happily ignore anything that was not assigned to a sli-gro-lay
        # WARNING: *if* the chosen clustering approach changes, one may need to start keeping track
        # of hits that do not get assigned to a sli/gro/lay.
        return np.delete(cids, np.where(cids == -1))

    def _setup_sligrolay_pdf(self, which: str = "slices") -> tuple[pd.DataFrame, np.ndarray]:
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
        cols = [
            "n_hits",  # Duplicate-corrected number of hits
            "perc",  # Duplicate-corrected hit percentage (in %)
            "okta",  # Corresponding okta value
            "height_base",  # Slice/Group/Layer base height
            "height_mean",  # Slice/Group/Layer mean height
            "height_std",  # Slice/Group/Layer height std
            "height_min",  # Slice/Group/Layer min height
            "height_max",  # Slice/Group/Layer max height
            "thickness",  # Slice/Group/Layer thickness
            "fluffiness",  # Slice/Group/Layer fluffiness
            "code",  # METAR code
            "significant",  # bool, whether this is a slice/group/layer that should be reported
            "cluster_id",  # Original id of the slice/group/layer set by the clustering algo
        ]

        # We want to raise early if 'which' is unknown.
        if which not in ["slices", "groups", "layers"]:
            raise AmpycloudError(
                f"Trying to initialize a data frame for {which}, "
                'which is unknown. Keyword arg "which" must be one of'
                '"slices", "groups" or "layers"'
            )

        # If I am looking at the slices, also keep track of whether they are isolated, or not.
        if which == "slices":
            cols += ["isolated"]

        # If I am looking at the groups, also keep track of how many sub-components they have
        if which == "groups":
            cols += ["ncomp"]

        # How many slices/groups/layers are there ?
        n_ind = getattr(self, f"n_{which}")

        # If we have None sli/gro/lay found, it means that they weren't computed yet.
        # Be unforgiving and raise an error.
        # Note: this is NOT the same as finding 0 sli/gro/lay, in which case n_ind would be 0.
        if n_ind is None:
            raise AmpycloudError(f"No {which} found. Have they been computed ?")

        # Prepare a pandas DataFrame to store all the info
        pdf = pd.DataFrame(index=range(n_ind), columns=cols)

        cluster_ids = self._get_cluster_ids(which)

        for ind, cid in enumerate(cluster_ids):
            if which == "groups":
                # Here, check if the layering was already done ... in which case one should NOT
                # be metarizing clusters ! This is one of those places where it is assumed that
                # the layering step comes *after* the grouping step.
                if self._layers is not None:
                    raise AmpycloudError(
                        "Layering already done."
                        " If you metarize your groups now, you will loose the"
                        " layering information !"
                    )
                # If all is as expected, then set the number of sub-components to -1 for now, until
                # the layering step decides otherwise (possibly).
                pdf.loc[ind, "ncomp"] = -1
            # Keep track of the original sli/gro/lay id
            pdf.loc[ind, "cluster_id"] = cid

        return pdf, cluster_ids

    def _calculate_cloud_amount(self, which: str, pdf: pd.DataFrame, cluster_ids: np.ndarray) -> pd.DataFrame:
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
            in_sligrolay = self.data[which[:-1] + "_id"] == cid
            # Compute the number of hits of this slice/group/layer for each ceilometer,
            # removing any duplicates.
            # I.e. if hit from layers 2 & 3 from ceilo 1 belong to this sli/gro/lay, count them as
            # one hit only.
            # **BUT** if two hits occur at the same time between ceilo 1 and ceilo 2, count them
            # both ! This is to be consistent with the theoretical max hit number per cloud layer,
            # which assume a max of 1 hit/ceilo/time step.
            hits_per_ceilo = [
                len(np.unique(self.data[in_sligrolay * (self.data["ceilo"] == ceilo)]["dt"])) for ceilo in self.ceilos
            ]
            pdf.iloc[ind, pdf.columns.get_loc("n_hits")] = np.sum(hits_per_ceilo)
            # Transform this into a percentage
            pdf.iloc[ind, pdf.columns.get_loc("perc")] = (
                pdf.iloc[ind, pdf.columns.get_loc("n_hits")] / self.max_hits_per_layer * 100
            )
            # Compute the corresponding okta level, not fogetting to account for possible buffers
            # for the 0 and 8 okta bins.
            if pdf.iloc[ind, pdf.columns.get_loc("n_hits")] <= self.prms["MAX_HITS_OKTA0"]:
                pdf.iloc[ind, pdf.columns.get_loc("okta")] = 0
            elif (self.max_hits_per_layer - pdf.iloc[ind, pdf.columns.get_loc("n_hits")]) <= self.prms[
                "MAX_HOLES_OKTA8"
            ]:
                pdf.iloc[ind, pdf.columns.get_loc("okta")] = 8
            else:
                pdf.iloc[ind, pdf.columns.get_loc("okta")] = int(
                    wmo.perc2okta(pdf.iloc[ind, pdf.columns.get_loc("perc")])[0]
                )

        return pdf

    def _add_sligrolay_information(self, which: str, pdf: pd.DataFrame, cluster_ids: np.ndarray) -> pd.DataFrame:
        """Add statistical properties to slices/ groups/ layers .

        Args:
            which (str): One of "slices", "groups" or "layers".
            pdf (pd.DataFrame): The data frame holding slices/ groups/ layers.
            cluster_ids (npt.ArrayLike): The original ids of the slices/
                groups/ layers.

        Returns:
            pd.DataFrame: with additional results in the columns height_min,
                height_mean, height_max, height_std, thickness, fluffiness.

        """
        for ind, cid in enumerate(cluster_ids):
            # Which hits are in this sli/gro/lay ?
            in_sligrolay = self.data[which[:-1] + "_id"] == cid
            # Measure the mean height and associated std of the layer
            pdf.iloc[ind, pdf.columns.get_loc("height_mean")] = self.data.loc[in_sligrolay, "height"].mean(skipna=True)
            pdf.iloc[ind, pdf.columns.get_loc("height_std")] = self.data.loc[in_sligrolay, "height"].std(skipna=True)
            # Let's also keep track of the min, max, thickness, and fluffiness values
            pdf.iloc[ind, pdf.columns.get_loc("height_min")] = self.data.loc[in_sligrolay, "height"].min(skipna=True)
            pdf.iloc[ind, pdf.columns.get_loc("height_max")] = self.data.loc[in_sligrolay, "height"].max(skipna=True)
            pdf.iloc[ind, pdf.columns.get_loc("thickness")] = (
                pdf.iloc[ind, pdf.columns.get_loc("height_max")] - pdf.iloc[ind, pdf.columns.get_loc("height_min")]
            )
            pdf.iloc[ind, pdf.columns.get_loc("fluffiness")], _ = fluffer.get_fluffiness(
                self.data.loc[in_sligrolay, ["dt", "height"]].values, **self.prms["LOWESS"]
            )

        return pdf

    def _calculate_sligrolay_base_height(self, which: str, pdf: pd.DataFrame, cluster_ids: np.ndarray) -> pd.DataFrame:
        """Calculate base height for all slices/ groups/ layers.

        Args:
            which (str): One of slices/ groups/ layers.
            pdf (pd.DataFrame): DF holding slices/ groups/ layers.
            cluster_ids (npt.ArrayLike): Original IDs of slices/ groups/ layers.

        Returns:
            pd.DataFrame: with calculatio results in column height_base

        """
        for ind, cid in enumerate(cluster_ids):
            # Which hits are in this sli/gro/lay ?
            in_sligrolay = self.data[which[:-1] + "_id"] == cid
            if self.prms["EXCLUDE_FOR_BASE_HEIGHT_CALC"] != []:
                in_sligrolay_filtered = in_sligrolay * self.data["ceilo"].apply(
                    lambda x: x not in self.prms["EXCLUDE_FOR_BASE_HEIGHT_CALC"]
                )
                # We require a minimum of hits by the filtered ceilos that belong to the layer
                # of interest. Otherwise fall back to using all ceilos for the calculation.
                if in_sligrolay_filtered.sum() > self.prms["MAX_HITS_OKTA0"]:
                    in_sligrolay = in_sligrolay_filtered
                else:
                    warnings.warn(
                        "Not enough data after filtering to calculate cloud base height, "
                        f"will fall back to use all data in group/ slice/ layer {cid}",
                        AmpycloudWarning,
                    )
            # Compute the base height
            pdf.iloc[ind, pdf.columns.get_loc("height_base")] = self._calculate_base_height_for_selection(in_sligrolay)
        return pdf

    @log_func_call(logger)
    def metarize(self, which: str = "slices") -> None:
        """Assembles a :py:class:`pandas.DataFrame` of slice/group/layer METAR properties of
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
            * ``height_base (float)``: base height
            * ``height_mean (float)``: mean height
            * ``height_std (float)``: height standard deviation
            * ``height_min (float)``: minimum height
            * ``height_max (float)``: maximum height
            * ``thickness (float)``: thickness
            * ``fluffiness (float)``: fluffiness (expressed in height units, i.e. ft)
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
            fact that clouds have a single base height at any given time [*citation needed*].

        Note:
            The metarize function is modularized in private submethods defined above.

        """

        # setup pd.DataFrame to store slices/ groups/ layers
        pdf, cids = self._setup_sligrolay_pdf(which)

        # calculate cloud amount in okta
        pdf = self._calculate_cloud_amount(which, pdf, cids)

        # calculate slice/ group/ layer base height
        pdf = self._calculate_sligrolay_base_height(which, pdf, cids)

        # collect some more information, including fluffiness
        pdf = self._add_sligrolay_information(which, pdf, cids)

        # Then loop through all of the layers/ groups/ slices and add METAR codes
        for ind, _ in enumerate(cids):
            pdf.iloc[ind, pdf.columns.get_loc("code")] = wmo.okta2code(
                pdf.iloc[ind, pdf.columns.get_loc("okta")]
            ) + wmo.height2code(pdf.iloc[ind, pdf.columns.get_loc("height_base")])

        # Set the proper column types
        for cname in ["n_hits", "okta", "cluster_id"]:
            pdf[cname] = pdf[cname].astype(int)
        for cname in [
            "perc",
            "height_base",
            "height_mean",
            "height_std",
            "height_min",
            "height_max",
            "thickness",
            "fluffiness",
        ]:
            pdf[cname] = pdf[cname].astype(float)
        for cname in ["code"]:
            pdf[cname] = pdf[cname].astype(str)
        for cname in ["significant"]:
            pdf[cname] = pdf[cname].astype(bool)

        if which == "slices":
            pdf["isolated"] = pdf["isolated"].astype(bool)
        if which == "groups":
            pdf["ncomp"] = pdf["ncomp"].astype(int)

        # Sort the table as a function of the base height of the sli/gro/lay.
        # This is why having the 'cluster_id' info is useful (so I remember which they are).
        pdf.sort_values("height_base", inplace=True)

        # Reset the index, 'cause I only need the one.
        pdf.reset_index(drop=True, inplace=True)

        # Almost done ... I just need to figure out which levels are significant.
        pdf.loc[:, "significant"] = icao.significant_cloud(pdf["okta"].to_list())

        # Finally, assign the outcome where it belongs.
        setattr(self, f"_{which}", pdf)

    def _ncd_or_nsc(self) -> str:
        """Return the METAR code for No Cloud Detected / No Significant Cloud.
        Decision based on the attribute self._clouds_above_msa_buffer.

        Returns:
            str: 'NCD' or 'NSC'

        """
        if self._clouds_above_msa_buffer:
            return "NSC"
        return "NCD"

    def metar_msg(self, which: str = "layers") -> str:
        """Construct a METAR-like message for the identified cloud slices, groups, or layers.

        Args:
            which (str, optional): whether to look at 'slices', 'groups', or 'layers'. Defaults to
                'layers'.

        Returns:
            str: the METAR-like message.

        Important:
            The ICAO's cloud layer selection rules applicable to METARs will be applied to create
            the resulting ``str`` ! See :py:func:`.icao.significant_cloud` for details.

        .. Caution::
            The Minimum Sector Altitude values set when
            the :py:class:`.CeiloChunk` instance **was initialized** will be applied ! If in doubt,
            the values used by this method are those set in the (parent) class
            attribute :py:attr:`.AbstractChunk.msa`

        """

        # Deal with the MSA: set it to infinity if None was specified
        if self.msa is None:
            msa_val = np.inf
        else:
            msa_val = self.msa

        # Some sanity checks to begin with
        if (sligrolay := getattr(self, which)) is None:
            raise AmpycloudError(f"No {which} information found. Have they been computed ?")

        # Deal with the 0 layer situation
        if getattr(self, f"n_{which}") == 0:
            return self._ncd_or_nsc()

        # Deal with the situation where layers have been found ...
        msg = sligrolay["code"]
        # What layers are significant *AND* below the MSA ?
        report = sligrolay["significant"] * (sligrolay["height_base"] < msa_val)
        msg = sligrolay["code"][report]
        msg = " ".join(msg.to_list())

        # Here, deal with the situations when all clouds are above the MSA
        if len(msg) == 0:
            # first check if any significant clouds are in the interval [MSA, MSA+MSA_HIT_BUFFER]
            sligrolay_in_buffer = sligrolay["significant"] * (sligrolay["height_base"] >= msa_val)
            if sligrolay_in_buffer.any():
                return "NSC"  # and return a NSC as it implies that the cloud is above the MSA
            return self._ncd_or_nsc()  # else, check for CBH above MSA + MSA_HIT_BUFFER

        return msg
