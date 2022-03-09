"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: pytest utilities
"""

# Import from python packages and modules
import pytest

def pytest_addoption(parser) -> None:
    """ A nifty little function that allows to feed command line arguments to the pytest command,
    e.g.:

        pytest --MPL_STYLE=latex

    Intended to enable the adjustment of the plotting style when running test locally.

    Reference:
        https://docs.pytest.org/en/6.2.x/example/simple.html#pass-different-values-to-a-test-function-depending-on-command-line-options

    """

    parser.addoption("--MPL_STYLE", action="store", default='base',
                     help="The required dynamic.MPL_STYLE value, e.g. latex or metsymb." +
                     " Defaults to base.")

    parser.addoption("--DO_SCIPLOTS", action="store_true", default=False,
                     help="If used, will generate the plots when running the scientific stability"+
                     "tests.")


@pytest.fixture(scope='session')
def mpls(request):
    """ A pytext fixture to identify whether the MPL_STYLE argument was fed to pytest, or not.

    Adapted from the similar function in dvas, which itself was adapted from the response of ipetrik
    on `StackOverflow <https://stackoverflow.com/questions/40880259>`__

    To use this, simply call it as an argument in any of the test function, e.g.:

        def test_some_func(a, b, mpls):
            ...
            if mpls:
                dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] = mpls

    """

    return request.config.getoption("--MPL_STYLE")

@pytest.fixture(scope='session')
def do_sciplots(request):
    """ A pytext fixture to decide whether to create plots (or not) when testing the
    scientific stability of ampycloud.

    Adapted from the similar function in dvas, which itself was adapted from the response of ipetrik
    on `StackOverflow <https://stackoverflow.com/questions/40880259>`__

    To use this, simply call it as an argument in any of the test function, e.g.:

            def test_some_func(a, b, do_sciplots):
            ...
            if do_sciplots:
                    diagnostic(...)

    """

    return request.config.getoption("--DO_SCIPLOTS")
