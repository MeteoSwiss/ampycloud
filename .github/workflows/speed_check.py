# -*- coding: utf-8 -*-
'''
Copyright (c) 2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

This script can be used together with a Github Action to check the speed of ampycloud is ok.

Created February 2022; F.P.A. Vogt; frederic.vogt@meteoswiss.ch
'''

from ampycloud.utils.performance import get_speed_benchmark

def main():
    ''' The one true function. '''

    # Run the default speed check
    (_, mean, std, _, _, _) = get_speed_benchmark()

    # Make sure that we remain below 1s at the 3 sigma level
    if (lim := mean + 3*std) >= 1:
        raise Exception('Ouch ! ampycloud speed check failed: mean + 3*std >= 1s ...')

    print(f'Speed check passed: mean + 3*std = {lim:.2f} s.')

if __name__ == '__main__':

    main()
