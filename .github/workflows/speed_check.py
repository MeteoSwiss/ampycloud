# -*- coding: utf-8 -*-
'''
Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

This script can be used together with a Github Action to check the speed of ampycloud is ok.

Created February 2022; F.P.A. Vogt; frederic.vogt@meteoswiss.ch
'''

import platform
import multiprocessing as mp
from ampycloud.utils.performance import get_speed_benchmark


def main():
    ''' The one true function. '''

    # Run the default speed check
    (_, mean, std, _, _, _) = get_speed_benchmark()

    print('Platform: %s' % (platform.platform()))
    print('CPU count: %i\n' % (mp.cpu_count()))
    print(f'Mean (std) processing time of the mock dataset: {mean:.2f} s ({std:.2f} s)')

    # Make sure that we remain below 1s at the 3 sigma level
    if (lim := mean + 3*std) >= 1:
        raise Exception('ampycloud speed check failed: mean + 3*std >= 1 s ...')

    print(f'Speed check passed: mean + 3*std = {lim:.2f} s < 1 s.')


if __name__ == '__main__':

    main()
