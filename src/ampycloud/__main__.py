"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: high-level entry point routines
"""

# Import from Python
import argparse
import platform
import multiprocessing as mp
from datetime import datetime

# Import from ampycloud
from .version import VERSION
from .utils import performance
from .core import copy_prm_file


def ampycloud_speed_test() -> None:
    """ The ampycloud_speed_test entry point, meant to by launched from the command line. """

    # Use argparse to make ampycloud user friendly
    parser = argparse.ArgumentParser(
        description='ampycloud {}'.format(VERSION) +
        ' - Python package to characterize cloud layers' +
        ' using ceilometer measurements.\n' +
        'This entry point lets you measure the performance of ampycloud on your machine.',
        epilog='For details: https://MeteoSwiss.github.io/ampycloud\n ',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-niter', action='store', default=10, type=int,
                        metavar='int',
                        help='Number of ampycloud.demo() executions to trigger. Defaults to 10.')

    # Done getting ready. Now start doing stuff.
    # What did the user type in ?
    args = parser.parse_args()

    # Launch the initialization of a new processing arena
    niter, mean, std, median, mmin, mmax = performance.get_speed_benchmark(niter=args.niter)

    print('\nTest datetime: %s' % (datetime.now()))
    print('Platform: %s' % (platform.platform()))
    print('CPU count: %i\n' % (mp.cpu_count()))

    print('ampycloud.demo() execution time from %i runs:' % niter)
    print(' * mean [std]: %.2fs [%.2fs]' % (mean, std))
    print(' * median [min; max]: %.2fs [%.2fs; %.2fs]\n' % (median, mmin, mmax))


def ampycloud_copy_prm_file() -> None:
    """ The ampycloud_copy_prm_file entry point, meant to be launched from the command line. """

    # Use argparse to make ampycloud user friendly
    parser = argparse.ArgumentParser(
        description='ampycloud {}'.format(VERSION) +
        ' - Python package to characterize cloud layers' +
        ' using ceilometer measurements.\n' +
        'This entry point lets you get a local copy the ampycloud parameter files.',
        epilog='For details: https://MeteoSwiss.github.io/ampycloud\n ',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-which', action='store', default='default', type=str,
                        metavar='name',
                        help='Name of the parameter file to copy. Defaults to "default".')

    # Done getting ready. Now start doing stuff.
    # What did the user type in ?
    args = parser.parse_args()

    # Get the local copy
    copy_prm_file(which=args.which)

    print('\nSuccess.')
