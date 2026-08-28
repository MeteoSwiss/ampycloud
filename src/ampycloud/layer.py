"""
Copyright (c) 2021-2026 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-CLause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: layering tools
"""

# Import from Python
import logging
import warnings
import copy
from typing import Union
import numpy as np
from sklearn.mixture import GaussianMixture

# Import from this module
from .errors import AmpycloudError, AmpycloudWarning
from .logger import log_func_call
from .scaler import minmax_scale
from .utils import utils

# Instantiate the module logger
logger = logging.getLogger(__name__)


@log_func_call(logger)
def scores2nrl(abics: np.ndarray) -> np.ndarray:
    """Converts AIC or BIC scores into probabilities = normalized relative likelihood.

    Args:
        abics (ndarray): scores.

    Returns:
        ndarray: probabilities of the different models.

    Specifically, this function computes:

    .. math::

        p_i = \\frac{e^{-0.5(\\textrm{abics}_i-min(\\textrm{abics}))}}{\\sum_{i}e^{-0.5(\\textrm{abics}_i-min(
        \\textrm{abics}))}}

    .. note::
        The smaller the BIC/AIC scores, the better, but the higher the probabilities = normalized
        relative likelihood, the better !

    """

    out = np.exp(-0.5 * (abics - np.min(abics)))
    out /= np.sum(out)

    return out


@log_func_call(logger)
def best_gmm(abics: np.ndarray, mode: str = "delta", min_prob: float = 1.0, delta_mul_gain: float = 1.0) -> int:
    """Identify which Gaussian Mixture Model is most appropriate given AIC or BIC scores.

    Args:
        abics (ndarray): the AICs or BICs scores, ordered from simplest to most complex model.
        mode (str, optional): one of ['delta', 'prob']. Defaults to 'delta'.
        min_prob (float, optional): minimum model probability computed from the scores's relative
            likelihood, below which the other models will be considered. Set it to 1 to select
            the model with the lowest score, irrespective of its probability. Defaults to 1.
            This has no effect unless mode='prob'.
        delta_mul_gain (float, optional): a smaller score will only be considered "valid"
            if it is smaller than delta_mul_gain*current_best_score. Defaults to 1.
            This has no effect unless mode='delta'.

    Returns:
        int: index of the "most appropriate" model.

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
            prob(abics[n]) > prob(abics[current_best_model])

        - `mode='delta'`:
          ::

            abics[n] < delta_mul_gain * abics[current_best_model]

        The default arguments of this function lead to selecting the number of components with the
        smallest score.

    """

    # How many models do I need to compare ?
    n_models = len(abics)

    # Compute the relative probabilities of each model from the scores,
    # i.e. compute the "relative likelihood" of each model, normalized by the sum of all relative
    # likelihoods (if warranted)
    if mode == "prob":
        nrl = scores2nrl(abics)

    # Now figure out if more than one components hides in the data.
    # This is not exact science, since ceilometer hits are not necessarily normally distributed.
    # Hence, rather than blindly select the smallest AICS/BICS values to decide if we have more than
    # 1 component, we start and stick with 1 component unless we notice a *significant* improvement
    # in the probabilities OR scores.
    # This is the whole reason for assessing models sequentially, and for asking users to feed
    # scores from the most simple to the least simple model.
    best_model_ind = 0
    for m_ind in range(n_models - 1):
        # Here, define if the new model is "better" following the user's wishes ...
        if mode == "prob":
            better = (nrl[best_model_ind] < min_prob) and (nrl[m_ind + 1] > nrl[best_model_ind])
        elif mode == "delta":
            better = abics[m_ind + 1] < delta_mul_gain * abics[best_model_ind]
        else:
            raise AmpycloudError(f"Unknown mode: {mode}")

        # If the requested conditions are met, then this next model is better !
        if better:
            best_model_ind = m_ind + 1

    return best_model_ind


def _check_min_sep_vs_resolution(vals_orig: np.ndarray, min_sep: Union[int, float]) -> None:
    """Warns if min_sep is too small compared to the data resolution, to flag a risk of
    over-layering."""

    res_orig = np.diff(np.sort(vals_orig.reshape(len(vals_orig))))
    res_orig = np.min(res_orig[res_orig > 0])
    logger.debug("res_orig: %.2f", res_orig)

    if min_sep < 5 * res_orig:
        warnings.warn(
            f"min_sep={min_sep} is smaller than 5*res_orig={5 * res_orig}."
            + "This could lead to an over-layering for thin groups !",
            AmpycloudWarning,
        )


def _fit_gmms(vals: np.ndarray, ncomp: np.ndarray, scores: str, random_seed: int) -> tuple:
    """Fits a GaussianMixture model for each candidate number of components, and computes the
    associated AIC/BIC scores."""

    models = {
        n_val: GaussianMixture(n_val, covariance_type="spherical", random_state=random_seed).fit(vals)
        for n_val in ncomp
    }

    if scores == "AIC":
        abics = np.array([model.aic(vals) for model in models.values()])
    elif scores == "BIC":
        abics = np.array([model.bic(vals) for model in models.values()])
    else:
        raise AmpycloudError(f"Unknown scores: {scores}")

    # Fix #119: at times, not all sub-layers may be populated by GaussianMixture.
    # To avoid problems down the line, we shall boost the abics score of such cases to make sure
    # they are NOT taken as the best model
    for n_id, n_val in enumerate(ncomp):
        if (n_eff := len(np.unique(models[n_val].predict(vals)))) < n_val:
            logger.warning(
                " %i out of %i sub-layers populated by GaussianMixture(%i) - see #119. "
                "Ruling out %i components as a possibility.",
                n_eff,
                n_val,
                n_val,
                n_val,
            )
            abics[n_id] = max(abics) + 1  # The larger the abics score, the worst the fit.

    return models, abics


def _merge_close_components(
    best_ids: np.ndarray, best_ncomp: int, base_comp_heights: list, min_sep: Union[int, float]
) -> tuple:
    """Merges components whose base heights are closer together than min_sep."""

    comp_ids = np.argsort(base_comp_heights)

    for ind, delta in enumerate(np.diff(np.sort(base_comp_heights))):
        # If the the delta is large enough, move on ...
        if delta >= min_sep:
            continue

        # Else, I have two components that are "too close" from each other. Let's merge them by
        # re-assigning the ids accordingly.
        best_ids[best_ids == comp_ids[ind + 1]] = comp_ids[ind]
        comp_ids[ind + 1] = comp_ids[ind]

        # Decrease the number of valid ids
        best_ncomp -= 1

    # Brief sanity check, to make sure I did not mess up
    assert len(np.unique(best_ids)) == best_ncomp, "Something very bad happened here ..."

    return best_ids, best_ncomp


def _fit_and_select_best_gmm(vals: np.ndarray, ncomp_max: int, scores: str, random_seed: int, **kwargs: dict) -> tuple:
    """Fits GMMs for 1 to ncomp_max components, and selects the best one."""

    ncomp = np.linspace(1, ncomp_max, ncomp_max, dtype=int)
    models, abics = _fit_gmms(vals, ncomp, scores, random_seed)

    best_model_ind = best_gmm(abics, **kwargs)
    best_ncomp = ncomp[best_model_ind]
    best_ids = models[ncomp[best_model_ind]].predict(vals)

    logger.debug(" %s scores: %s", scores, abics)
    logger.debug(" best_model_ind (raw): %i", best_model_ind)
    logger.debug(" best_ncomp (raw): %i", best_ncomp)

    return best_ncomp, best_ids, abics


@log_func_call(logger)
def ncomp_from_gmm(
    vals: np.ndarray,
    ncomp_max: int = 3,
    min_sep: Union[int, float] = 0,
    layer_base_params: Union[dict[str, int], None] = None,
    scores: str = "BIC",
    rescale_0_to_x: Union[float, None] = None,
    random_seed: int = 42,
    **kwargs: dict,
) -> tuple:
    """Runs a Gaussian Mixture Model on 1-D data, to determine if it contains 1, 2, or 3
    components.

    Args:
        vals (ndarray): the data to process. If ndarray is 1-D, it will be reshaped to 2-D via
            .reshape(-1, 1).
        ncomp_max (int, optional): maximum number of Gaussian components to assess. Defaults to 3.
        min_sep (int|float, optional): minimum separation, in data unit,
            required between the mean location of two Gaussian components to consider them distinct.
            Defaults to 0. This is used in complement to any parameters fed to best_gmm(), that will
            first decide how many components looks "best", at which point these may get merged
            depending on min_sep. I.e. min_sep does not lead to re-running the GMM, it only merges
            the identified layers if required.
        layer_base_params: Defined ampycloud parameters.
        scores (str, optional): either 'BIC' or 'AIC', to use Baysian Information Criterion or
            Akaike Information criterion scores.
        rescale_0_to_x (float, optional): if set, vals will be rescaled between 0 and this value
            before running the Gaussian Mixture Modelling. Defaults to None = no rescaling.
        random_seed (int, optional): used to reset **temporarily** the value of
            :py:func:`numpy.random.seed` to ensure repeatable results. Defaults to 42, because it
            is the Answer to the Ultimate Question of Life, the Universe, and Everything.
        **kwargs (dict, optional): these will be fed to `best_gmm()`.

    Returns:
        int, ndarray, ndarray: number of (likely) components, array of component ids to which
        each hit most likely belongs, array of AIC/BIC scores.

    The default values lead to selecting the number of components with the smallest BIC values.

    Note:
        This function was inspired from the "1-D Gaussian Mixture Model" example from astroML:
        `<https://www.astroml.org/book_figures/chapter4/fig_GMM_1D.html>`_
    """

    if layer_base_params is None:
        layer_base_params = {"lookback_perc": 100, "height_perc": 5}

    # If I get a 1-D array, deal with it.
    if np.ndim(vals) == 1:
        vals = vals.reshape(-1, 1)

    # Keep track of the original values
    vals_orig = copy.deepcopy(vals)

    # If all the points are the same, I should not bother doing anything ...
    n_unique = len(np.unique(vals_orig))
    if n_unique == 1:
        logger.debug("Skipping the GMM computation: all the values are the same.")
        return (1, np.zeros(len(vals_orig)), None)
    if n_unique < ncomp_max:
        ncomp_max = n_unique
        warnings.warn(f"Restricting ncomp_max to the max number of individual values: {ncomp_max}")

    # Is min_sep sufficiently large, given the data resolution ? If not, we we end up with some
    # over-layering.
    _check_min_sep_vs_resolution(vals_orig, min_sep)

    # Rescale the data if warranted
    if rescale_0_to_x is not None:
        vals = minmax_scale(vals) * rescale_0_to_x

    # Fit GMMs for 1 to ncomp_max components, and select the best one
    best_ncomp, best_ids, abics = _fit_and_select_best_gmm(vals, ncomp_max, scores, random_seed, **kwargs)

    # If I found only one component, I can stop here
    if best_ncomp == 1:
        return best_ncomp, best_ids, abics

    # If I found more than one component, let's make sure that they are sufficiently far apart.
    # First, let's compute the component base height
    base_comp_heights = [
        utils.calc_base_height(
            vals_orig[best_ids == i].flatten(), layer_base_params["lookback_perc"], layer_base_params["height_perc"]
        )
        for i in range(best_ncomp)
    ]

    # These may not be ordered, so let's keep track of the indices, and merge those that are not
    # sufficiently far apart.
    best_ids, best_ncomp = _merge_close_components(best_ids, best_ncomp, base_comp_heights, min_sep)

    logger.debug("best_ncomp (final): %i", best_ncomp)

    return best_ncomp, best_ids, abics
