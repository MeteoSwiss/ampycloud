"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: dynamic parameters, which can be altered during execution.
"""

#: str: Style to use for the plots. Can be 'none', 'base', 'nolatex', 'latex', 'metsymb'
MPL_STYLE : str = 'none'

#: int: Max sky coverage (in %) up to which the coverage is considered null.
OKTA_LIM0 : int = 2

#: int: Min sky coverage (in %) down to which the coverage is considered full.
OKTA_LIM8 : int = 98

#: float: Fraction of smallest layer points to median to compute the layer altitude for the METAR
LAYER_BASE_FRAC : float = 0.1

#: dict: Slicing parameters
SLICING_PRMS : dict = {
    # Clustering algorithm name
    'algo': 'agglomerative',
    # Clustering algorithm parameters
    'algo_kwargs': {'n_clusters': None,
                    'distance_threshold': 0.2,
                    'linkage': 'average',
                    'affinity': 'manhattan'
                    },
    # Time scaling mode
    'dt_scale_mode': 'const',
    # Time scaling parameters
    'dt_scale_kwargs': {'scale': 100000,
                        'mode': 'scale'
                        },
    # Altitude scaling mode
    'alt_scale_mode': 'minmax',
    # Altitude scaling parameters
    'alt_scale_kwargs': {'min_range': 1000,
                         'mode': 'scale'}
    }

#: dict: Clustering parameters
GROUPING_PRMS : dict = {
    # Grouping algorithm name
    'algo': 'agglomerative',
    # Grouping algorithm parameters
    'algo_kwargs': {'n_clusters': None,
                    'distance_threshold': 1,
                    'linkage': 'single',
                    'affinity': 'manhattan'
                    },
    # Time scaling mode
    'dt_scale_mode': 'const',
    # Time scaling parameters
    'dt_scale_kwargs': {'scale': 180,
                        'mode': 'scale'},
    # Altitude scaling mode
    'alt_scale_mode': 'step',
    # Altitude scaling parameters
    'alt_scale_kwargs': {'steps': [8000, 14000],
                         'scales': [100, 500, 1000],
                         'mode': 'scale'},
    # Distance from the mean altitude (in std) below which two slices are considered "overlapping"
    'overlap': 2.
    }

#: dict: Layering parameters
LAYERING_PRMS : dict = {
    # Minimum okta value below which cluster splitting is not attempted
    'min_okta_to_split': 2,
    # Gaussian Mixture Model parameters
    'gmm_kwargs': {
        # Whether to use 'BIC' or 'AIC' scores to decide which model is "best".
        'scores': 'BIC',
        # Whether to use 'delta', or 'prob' to find the best model.
        # See ampycloud.layer.best_gmm() for details.
        'mode': 'delta',
        # minimum model probability computed from the relative likelihood,
        # below which alternative models with more components will be considered.
        # Only used if mode ='prob'
        'min_prob': 0.01,
        # a model with a smaller score will only be considered "valid"
        # if its score is smaller than delta_mul_gain*current_best_score.
        # Only used if mode='delta'
        'delta_mul_gain': 0.95,
        # If set, rescale each group between 0 and this value before looking for layers using gmm.
        'rescale_0to': 100,
        },
    }
