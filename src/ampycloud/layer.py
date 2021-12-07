"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-CLause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: layering tools
"""

# Import from Python
import logging
import numpy as np
from sklearn.mixture import GaussianMixture

# Import from this module
from .errors import AmpycloudError
from .logger import log_func_call
from .scaler import minmax_scaling

# Instantiate the module logger
logger = logging.getLogger(__name__)

@log_func_call(logger)
def scores2nrl(abics : np.ndarray) -> np.ndarray:
    """ Converts AIC or BIC scores into probabilities = normalized relative likelihood.

    Specifically, this function computes:

    .. math::

        p_i = \\frac{e^{-0.5(\\textrm{abics}_i-min(\\textrm{abics}))}}{\\sum_{i}e^{-0.5(\\textrm{abics}_i-min(\\textrm{abics}))}}

    Args:
        abics (ndarray): scores.

    Returns:
        ndarray: probabilities of the different models.
    """

    out = np.exp(-0.5*(abics-np.min(abics)))
    out /= np.sum(out)

    return out

@log_func_call(logger)
def best_gmm(abics : np.ndarray, mode : str = 'delta',
             min_prob : float = 1., delta_mul_gain : float = 1.) -> int:
    """ Identify which Gaussian Mixture Model is most appropriate given AIC or BIC scores.

    Model selection can be based on:

        1. the normalized relative likelihood values (see `scores2nrl()`) of the AIC or/and BIC
        scores, or
        2. the normalized absolute offsets between the AIC or BIC scores.

    The mode defaults to 'delta', i.e. the normalized absolute offsets between the scores scores.

    Note:
        The order of the scores **does matter** for this routine.

        Starting with the first model as the "current best model", the model n will become the
        "current best model" if:

        - `mode='prob'`:
          ::

            prob(abics[current_best_model]) < min_prob
            AND
            abics[n] < abics[current_best_model]

        - `mode='delta'`:
          ::

            abics[n] < delta_mul_gain * abics[current_best_model]

        The default arguments of this function lead to selecting the number of components with the
        smallest score.

    Args:
        abics (ndarray): the AICs or BICs values, ordered from simplest to most complex model.
        mode (str, optional): one of ['delta', 'prob']. Defaults to 'delta'.
        min_prob (float, optional): minimum model probability computed from the scores's relative
            likelihood, below which alternative models will be considered. Set it to 1 to select
            the model with the lowest score, irrespective of its probability. Defaults to 1.
            This has no effect unless mode='prob'.
        delta_mul_gain (float, optional): a smaller score will only be considered "valid"
            if it is smaller than delta_mul_gain*current_best_score. Defaults to 1.
            This has no effect unless mode='delta'.

    Returns:
        int: index of the "most appropriate" model.

    """

    # How many models do I need to compare ?
    n_models = len(abics)

    # Compute the relative probabilities of each model from the scores,
    # i.e. compute the "relative likelihood" of each model, normalized by the sum of all relative
    # lieklihoods (if warranted)
    if mode=='prob':
        nrl = scores2nrl(abics)

    # Now figure out if more than one components hides in the data.
    # This is not exact science, since ceilometer hits are not necessarily normally distributed.
    # Hence, rather than blindly select the smallest AICS/BICS values to decide if we have more than
    # 1 component, we start and stick with 1 component unless we notice a *significant* improvement
    # in the probabilities OR scores.
    # This is the whole reason for assessing models sequentially, and for asking users to feed
    # scores from the most simple to the least simple model.
    best_model_ind = 0
    for m_ind in range(n_models-1):
        # Here, define if the new model is "better" following the user's wishes ...
        if mode == 'prob':
            better = (nrl[best_model_ind] < min_prob) and \
                     (abics[m_ind+1] < abics[best_model_ind])
        elif mode == 'delta':
            better = abics[m_ind + 1] < delta_mul_gain * abics[best_model_ind]
        else:
            raise AmpycloudError(f'Ouch ! Unknown mode: {mode}')

        # If the requested conditions are met, then this next model is better !
        if better:
            best_model_ind = m_ind + 1

    return best_model_ind

@log_func_call(logger)
def ncomp_from_gmm(vals : np.ndarray,
                   scores : str = 'BIC',
                   rescale_0to : float = None,
                   **kwargs : dict) -> tuple:
    """ Runs a Gaussian Mixture Model on 1-D data, to determine if it contains 1, 2, or 3
    components.

    The default values lead to selecting the number of components with the smallest BIC values.

    Args:
        vals (ndarray): the data to process. If ndarray is 1-D, it will be reshaped to 2-D via
            .reshape(-1, 1).
        scores (str, optional): either 'BIC' or 'AIC', to use Baysian Information Criterion or
            Akaike Information criterion scores.
        rescale_0to (float, optional): if set, vals will be rescaled between 0 and this value.
            Defaults to None = no rescaling.
        **kwargs (dict, optional): these will be fed to `best_gmm()`.

    Returns:
        int, ndarray, ndarray: number of (likely) components, array of component ids to which
        each hit most likely belongs, array of AIC/BIC scores.

    Note:
        This function was inspired from the "1-D Gaussian Mixture Model" example from astroML:
        `<https://www.astroml.org/book_figures/chapter4/fig_GMM_1D.html>`_
    """

    # If I get a 1-D array, deal with it.
    if np.ndim(vals) == 1:
        vals = vals.reshape(-1, 1)

    # Rescale the data if warranted
    if rescale_0to is not None:
        vals = minmax_scaling(vals, min_range=0) * rescale_0to

    # I will only look for at most 3 layers.
    ncomp = np.array([1, 2, 3])

    # Prepare to store the different model fits
    models = {}

    # Run the Gaussian Mixture fit for all cases ... should we do anything more fancy here ?
    for n_val in ncomp:
        models[n_val] = GaussianMixture(n_val, covariance_type='spherical').fit(vals)

    # Extract the AICS and BICS scores
    if scores == 'AIC':
        abics = np.array([models[item].aic(vals) for item in models])
    elif scores == 'BIC':
        abics = np.array([models[item].bic(vals) for item in models])
    else:
        raise AmpycloudError(f'Ouch ! Unknown scores: {scores}')

    best_model_ind = best_gmm(abics, **kwargs)

    logger.debug('%s scores: %s', scores, abics)
    logger.debug('best_model_ind: %i', best_model_ind)

    return ncomp[best_model_ind], models[ncomp[best_model_ind]].predict(vals), abics
