"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: clustering tools
"""

# Import from Python
import logging
from typing import Union
import numpy as np
from sklearn.cluster import AgglomerativeClustering

# Import from ampycloud
from .errors import AmpycloudError
from .logger import log_func_call

# Instantiate the module logger
logger = logging.getLogger(__name__)


@log_func_call(logger)
def agglomerative_cluster(data: np.ndarray, n_clusters: int = None,
                          affinity: str = 'euclidean', linkage: str = 'single',
                          distance_threshold: Union[int, float] = 1) -> tuple:
    """ Function that wraps arround :py:class:`sklearn.cluster.AgglomerativeClustering`.

    Args:
        data (ndarray): array of [x, y] pairs to run the clustering on.
        n_clusters (int, optional): see :py:class:`sklearn.cluster.AgglomerativeClustering`
            for details. Defaults to None.
        affinity (str, optional): see :py:class:`sklearn.cluster.AgglomerativeClustering` for
            details. Defaults to 'euclidian'.
        linkage (str, optional): see :py:class:`sklearn.cluster.AgglomerativeClustering` for
            details. Defaults to 'single'.
        distance_threshold (int|float, optional): see
            :py:class:`sklearn.cluster.AgglomerativeClustering` for details. Defaults to 1.

    Returns:
        int, ndarray: number of clusters found, and corresponding clustering labels for each data
        point.

    """

    # Set things up
    agg_clu = AgglomerativeClustering(linkage=linkage, n_clusters=n_clusters, affinity=affinity,
                                      distance_threshold=distance_threshold).fit(data)

    # Return the stuff of interest
    return agg_clu.n_clusters_, agg_clu.labels_


@log_func_call(logger)
def clusterize(data: np.ndarray, algo: str = None, **kwargs: dict) -> tuple:
    """ Umbrella clustering routine, that provides a single access point to the different clustering
    algorithms.

    Args:
        data (ndarray): array of [x, y] arrays to clusterize.
        algo (str, optional): clustering algorithm, that must be one of [None, 'agglomerative'].
            Defaults to None.
        kwargs (dict, optional): keyword arguments to be fed to the underlying clustering function.

    Returns:
        int, ndarray: the number of clusters identified, and the associated labels for each data
        point.

    """

    # If I was asked to do nothing, then do nothing ...
    if algo is None:
        return None

    # Launch the requested clustering algorithm, feeding it the user-supplied keywords.
    if algo == 'agglomerative':
        return agglomerative_cluster(data, **kwargs)

    # Else, complain ...
    raise AmpycloudError(f'Ouch ! Clustering algorithm unknown: {algo}')
