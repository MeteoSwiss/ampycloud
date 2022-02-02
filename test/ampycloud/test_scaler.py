"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the scaler module
"""

# Import from Python
from pytest import raises
import numpy as np

# Import from this package
from ampycloud.scaler import shift_and_scale, minmax_scale, minrange2minmax, step_scale
from ampycloud.scaler import convert_kwargs, apply_scaling
from ampycloud.errors import AmpycloudError

def test_shift_and_scale():
    """ Test the shift_and_scale routine. """

    assert shift_and_scale(np.ones(1), shift=0, scale=10, mode='do') == 0.1
    assert np.isnan(shift_and_scale(np.array([1, np.nan]), mode='do')[1])
    assert shift_and_scale(np.ones(1), scale=10, mode='do') == 0
    assert shift_and_scale(np.ones(1), shift=0, mode='do') == 1
    assert np.all(shift_and_scale(np.array([1, 2]), scale=10, mode='do') == np.array([-0.1, 0]))
    assert shift_and_scale(np.zeros(1), shift=10, scale=10, mode='undo') == 10
    assert np.all(shift_and_scale(np.array([7e5,7e5+1,7e5+2]), scale=10, mode='do') == \
        np.array([-0.2, -0.1, 0]))
    tmp = np.array([1, 12, 3])
    # Check that this is indeed circular
    assert np.all(shift_and_scale(shift_and_scale(tmp, scale=11, mode='do'),
        scale=11, mode='undo', shift=np.nanmax(tmp)) == tmp)

def test_minmax_scale():
    """ Test the minmax_scaling function, inculding the descaling mode. """

    # Generate random values, making sure they span a large enough range
    vals = np.random.random(size=15) * 1e4

    # Add a nan for good measure
    vals[0] = np.nan

    out = minmax_scale(vals, mode='do')
    deout = minmax_scale(out, min_val=np.nanmin(vals), max_val=np.nanmax(vals), mode='undo')

    # Check conversion is between 0 and 1
    assert np.nanmax(out) <= 1
    assert np.nanmin(out) >= 0
    # Check de-scaling works
    assert np.all(np.round(deout[~np.isnan(vals)], 5) == np.round(vals[~np.isnan(vals)], 5))
    # Check NaNs stay NaNs
    assert np.all(np.isnan(deout[np.isnan(vals)]))

def test_step_scale():
    """ Test the step scale function. """

    steps = [10, 20]
    scales = [10, 100, 1000]

    vals = np.array([-1, 5, 15, 25, 35])

    out = step_scale(vals, steps=steps, scales=scales, mode='do')
    assert np.all(out == np.array([-0.1, 0.5, 1.05, 1.105, 1.115]))

    deout = step_scale(out, steps=steps, scales=scales, mode='undo')
    assert np.all(np.round(deout, 1) == vals)

    # Check the continuity condition
    vals = np.arange(0, 25000, 10)
    out = step_scale(vals, steps=[3000, 7000, 10000, 14000], scales=[100, 500, 50, 1000, 10],
                       mode='do')
    # Basic check to make sure we are always increasing
    assert np.all(np.diff(out) > 0)
    # Check for gaps by looking at the slopes
    # If a slope value were to appear only once, it would be a gap.
    assert np.all([np.count_nonzero(np.diff(out)==item) for item in np.unique(np.diff(out))])
    # Check I can undo the scaling
    deout = step_scale(out, steps=[3000, 7000, 10000, 14000], scales=[100, 500, 50, 1000, 10],
                         mode='undo')
    assert np.all(np.round(deout, 1) == vals)

def test_convert_kwargs():
    """ Test the convert_kwargs() function """

    data = np.array([1, 2, 10])
    kwargs = {'min_range': 5}

    # 'min_range' is a "user" keyword
    out = convert_kwargs(data, fct='minmax-scale', **kwargs)
    assert 'min_range' not in out.keys()
    assert 'min_val' in out.keys()
    assert 'max_val' in out.keys()

    kwargs = {}
    assert 'shift' in convert_kwargs(data, fct='shift-and-scale', **kwargs).keys()


def test_apply_scaling():
    """ Test the umbrella scaling function, and its ability to correctly summon the different
    scaling functions. """

    out = apply_scaling(np.ones(1), fct='shift-and-scale', scale=10, mode='do')
    assert out == 0

    out = apply_scaling(np.array((10, 20)), fct='shift-and-scale', scale=10, shift=15, mode='do')
    assert (out == np.array([-0.5, 0.5])).all()

    # Try to feed args in the wrong order ...
    out = apply_scaling(np.ones(1), fct='step-scale', scales=[10, 100, 1000], mode='do',
                        steps=[10, 20])
    assert out == 0.1

    # Try to feed only NaNs
    out = apply_scaling(np.ones(10)*np.nan, fct='minmax-scale', mode='do', min_range=1000)
    assert np.all(np.isnan(out))

    # Try when a single point is being fed
    out = apply_scaling(np.ones(1), fct='minmax-scale', mode='do', min_range=1000)
    assert out == 0.5

    # Try with a min-range
    din = np.array([1,5,9])
    out = apply_scaling(din, fct='minmax-scale', min_range=10, mode='do')
    assert np.all(out == np.array([0.1, 0.5, 0.9]))

    # Make sure undoing the minmax-scale without enough info crashes properly.
    with raises(AmpycloudError):
        apply_scaling(out, fct='minmax-scale', mode='undo')

    # Now actually try the undoing
    (min_val, max_val) = minrange2minmax(din, min_range=10)
    reout = apply_scaling(out, fct='minmax-scale', mode='undo', min_val=min_val, max_val=max_val)
    assert np.all(reout == din)
