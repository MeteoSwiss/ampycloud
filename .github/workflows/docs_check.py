# -*- coding: utf-8 -*-
'''
Copyright (c) 2020-2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the GNU General Public License v3.0 or later.

SPDX-License-Identifier: GPL-3.0-or-later

This script can be used together with a Github Action to build the docs, and check for errors and
warnings. This script assumes that one is located within the "docs" folder.

Created June 2020; F.P.A. Vogt; frederic.vogt@meteoswiss.ch
'''

import subprocess

def main():
    ''' The one true function. '''

    # Run the doc building script, and collect the output.
    # Adapted from:
    # https://stackoverflow.com/questions/4760215/running-shell-command-and-capturing-the-output
    # Author: senderle
    result = subprocess.run(['sh', './build_docs.sh'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    lines = result.stdout.decode('utf-8').split('\n')
    warn_lines = result.stderr.decode('utf-8').split('\n')

    if len(warn_lines) > 1:
        # Something went wrong: display the relevant info
        print('Something went wrong when generating the docs:')
        print(' ')
        for warn in warn_lines:
            print(warn)

        raise Exception('Ouch ! Some errors/warning were detected when building the docs.')

    # Docs compiled ok. Print the log FYI.
    print('Docs compiled ok. Logs follow.')
    for line in lines:
        print(line)

if __name__ == '__main__':

    main()
