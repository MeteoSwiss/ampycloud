"""
Copyright (c) 2021-2026 MeteoSwiss, contributors listed in AUTHORS.

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
import pandas as pd

# Import from this package
from .logger import log_func_call
from . import dynamic, hardcoded
from .utils import utils

# Instantiate the module logger
logger = logging.getLogger(__name__)


class AbstractChunk(ABC):
    """Abstract parent class for data chunk classes."""

    #: dict: required data columns
    DATA_COLS = copy.deepcopy(hardcoded.REQ_DATA_COLS)

    @abstractmethod
    def __init__(
        self,
        data: pd.DataFrame,
        prms: Optional[dict] = None,
        geoloc: Optional[str] = None,
        ref_dt: Optional[str] = None,
    ) -> None:
        """Init routine for abstract class."""

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
        """The Minimum Sector Altitude set when initializing this specific instance, in ft aal."""
        return self.prms["MSA"]

    @property
    def msa_hit_buffer(self) -> float:
        """The Minimum Sector Altitude hit buffer set when initializing this specific instance,
        in ft."""
        return self.prms["MSA_HIT_BUFFER"]

    @property
    def data(self) -> pd.DataFrame:
        """The data of the chunk, as a pandas DataFrame."""
        return self._data

    @property
    def geoloc(self) -> Union[str, None]:
        """The name of the geographic location of the observations."""
        return self._geoloc

    @property
    def ref_dt(self) -> Union[str, None]:
        """The reference date and time for the data, i.e. Delta t = 0."""
        return self._ref_dt

    @property
    def prms(self) -> dict:
        """The dictionnary of ampycloud parameters set at the init of this class instance."""
        return self._prms

    @log_func_call(logger)
    def _cleanup_pdf(self, data: pd.DataFrame) -> pd.DataFrame:
        """Checks the input pandas DataFrame and adjust it as required.

        Args:
            data (pd.DataFrame): the input data.

        """

        # Begin with a thorough inspection of the dataset
        data = utils.check_data_consistency(data, req_cols=self.DATA_COLS)

        # By default we set this flag to false and overwrite if enough hits are present
        self._clouds_above_msa_buffer = False

        # Drop any hits that are too high and check if they exceed the threshold for 1 OKTA
        # if yes, set the flag clouds_above_msa_buffer to True
        if self.msa is not None:
            hit_height_lim = self.msa + self.msa_hit_buffer
            logger.info("Cropping hits above MSA+buffer: %s ft", str(hit_height_lim))
            # First layer and vervis hits above the cut threshold get turned to NaNs, to signal a
            # non-detection below the MSA. Also change the hit type to 0 accordingly in order
            # to create a "no hit detected" in the range of interest (i.e. below MSA).
            above_msa_t1_or_less = data[(data.height > hit_height_lim) & (data.type <= 1)].index
            data.loc[above_msa_t1_or_less, "type"] = 0
            data.loc[above_msa_t1_or_less, "height"] = np.nan
            # Type 2 or more hits get cropped (there should be only 1 non-detection per time-stamp).
            above_msa_t2_or_more = data[(data.height > hit_height_lim) & (data.type > 1)].index
            data = data.drop(above_msa_t2_or_more)
            if len(above_msa_t1_or_less) + len(above_msa_t2_or_more) > self._prms["MAX_HITS_OKTA0"]:
                logger.info(
                    "Hits above MSA + MSA_HIT_BUFFER exceeded threshold MAX_HITS_OKTA0. Will add "
                    "flag 'high_clouds_detected' to indicate the presence of high clouds."
                )
                self._clouds_above_msa_buffer = True

        return data

    @log_func_call(logger)
    def _setup_prms(self, prms: dict) -> dict:
        """Setup a full dict of ampycloud prms given a user input, using default prms where
        necessary."""

        # First, get a deep copy of the (current) default prms
        full_prms = copy.deepcopy(dynamic.AMPYCLOUD_PRMS)

        # Adjust the prms as warranted by the user
        if prms is not None:
            full_prms = utils.adjust_nested_dict(full_prms, prms)

        return full_prms
