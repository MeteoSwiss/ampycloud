"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the BSD-3-Clause license.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the scaler module
"""

# Import from Python
import numpy as np

# Import from this package
from ampycloud.scaler import const_scaling, minmax_scaling, step_scaling, scaling


def test_const_scaling():
    """ Test the const_scaling routine. """

    assert const_scaling(np.ones(1), 10, mode='scale') == 0.1
    assert const_scaling(np.ones(1), 10, mode='descale') == 10

def test_minmax_scaling():
    """ Test the minmax_scaling function, inculding the descaling mode. """

    # Generate random values, making sure they span a large enough range
    vals = np.random.random(size=15) * 1e4

    # Add a nan for good measure
    vals[0] = np.nan

    out = minmax_scaling(vals, min_range=1000, mode='scale')
    deout = minmax_scaling(out, min_range=1000, mode='descale', min_val=np.nanmin(vals),
                           max_val=np.nanmax(vals))

    # Check conversion is between 0 and 1
    assert np.nanmax(out) <= 1
    assert np.nanmin(out) >= 0
    # Check de-scaling works
    assert np.all(np.round(deout[~np.isnan(vals)], 5) == np.round(vals[~np.isnan(vals)], 5))
    # Check NaNs stay NaNs
    assert np.all(np.isnan(deout[np.isnan(vals)]))

    # Repeat, this time with a min-range
    vals = np.array([100, 200, 400])

    out = minmax_scaling(vals, min_range=1000, mode='scale')
    deout = minmax_scaling(out, min_range=1000, mode='descale', min_val=np.nanmin(vals),
                           max_val=np.nanmax(vals))

    # Make sure we are between 0 and 1
    assert np.nanmax(out) <= 1
    assert np.nanmin(out) >= 0
    # Go further and make sure we re actually much smaller than that
    assert np.round(np.nanmax(out)-np.nanmin(out), 1) == 0.3
    # Check that all gets properly descaled as well
    assert np.all(np.round(deout[~np.isnan(vals)], 5) == np.round(vals[~np.isnan(vals)], 5))

def test_step_scaling():
    """ test the step scaling function. """


    steps = [10, 20]
    scales = [10, 100, 1000]

    vals = np.array([-1, 5, 15, 25, 35])

    out = step_scaling(vals, steps=steps, scales=scales, mode='scale')
    assert np.all(out == np.array([-0.1, 0.5, 1.05, 1.105, 1.115]))

    deout = step_scaling(out, steps=steps, scales=scales, mode='descale')
    assert np.all(np.round(deout, 1) == vals)

    # Check the continuity condition
    vals = np.arange(0, 25000, 10)
    out = step_scaling(vals, steps=[3000, 7000, 10000, 14000], scales=[100, 500, 50, 1000, 10],
                       mode='scale')
    assert np.all(np.diff(out) > 0)
    deout = step_scaling(out, steps=[3000, 7000, 10000, 14000], scales=[100, 500, 50, 1000, 10],
                         mode='descale')
    assert np.all(np.round(deout, 1) == vals)

def test_scaling():
    """ test the umbrella scaling function, and its ability to correctly summon the different
    scaling functions. """

    out = scaling(np.ones(1), fct='const', scale=10, mode='scale')
    assert out == 0.1

    # Try to feed args in the wrong order ...
    out = scaling(np.ones(1), fct='step', scales=[10, 100, 1000],
                  mode='scale', steps=[10, 20])
    assert out == 0.1

    # Try to feed only NaNs
    out = scaling(np.ones(10)*np.nan, fct='minmax', mode='scale', min_range=1000)
    assert np.all(np.isnan(out))

    # Try other problematic cases that should only return NaNs
    out = scaling(np.ones(1), fct='minmax', mode='scale', min_range=1000)
    assert np.all(np.isnan(out))

    out = scaling(np.ones(1), fct='minmax', mode='scale', min_range=-1)
    assert np.all(np.isnan(out))
