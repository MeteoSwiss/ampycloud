# -*- coding: utf-8 -*-
'''
Copyright (c) 2020-2022 MeteoSwiss, created by F.P.A. Vogt; frederic.vogt@meteoswiss.ch

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

This script can be used together with a Github Action to run pylint on all the .py files in a
repository. Command line arguments can be used to search for a specific subset of errors (if any are
found, this script will raise an Exception), or to ignore some errors in a generic search (which
will print all the errors found, but will not raise any Exception). If a score is specified, the
script will raise an Exception if it is not met.

Created May 2020; fpavogt; frederic.vogt@meteoswiss.ch
Adapted Jan 2022; fpavogt; frederic.vogt@meteoswiss.ch
'''

import argparse
import glob
import os
import re
from pylint import epylint as lint


def main():
    ''' The main function. '''

    # Use argparse to allow to feed parameters to this script
    parser = argparse.ArgumentParser(description='''Runs pylint on all .py files in a folder and all
                                                    its subfolders. Intended to be used with a
                                                    Github Action.''',
                                     epilog='Feedback, questions, comments: \
                                             frederic.vogt@meteoswiss.ch \n',
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--restrict', action='store', metavar='error codes', nargs='+',
                        default=None, help='''List of space-separated error codes to strictly
                                            restrict the search for.
                                            To see all possible codes: pylint --list-msgs''')

    parser.add_argument('--exclude', action='store', metavar='error codes', nargs='+',
                        default=None, help='List of space-separated error codes to ignore.')

    parser.add_argument('--min_score', type=float, action='store', metavar='float<10', default=None,
                        help='Minimum acceptable score, below which an Exception should be raised')

    # What did the user type in ?
    args = parser.parse_args()

    # Do I want to only run pylint for a specific few errors ONLY ?
    if args.restrict is not None:

        error_codes = ','.join(args.restrict)
        pylint_command = '--disable=all --enable='+error_codes

    # or do I rather want to simply exclude some errors ?
    elif args.exclude is not None:
        error_codes = ','.join(args.exclude)
        pylint_command = '--disable='+error_codes

    else:  # just run pylint without tweaks

        pylint_command = ''

    # Get a list of all the .py files here and in all the subfolders.
    fn_list = glob.glob(os.path.join('.', '**', '*.py'), recursive=True)

    # Skip the docs and build folders
    for bad_item in [os.path.join('.', 'build'), os.path.join('.', 'docs')]:
        fn_list = [item for item in fn_list if bad_item not in item]

    # Turn this into a string to feed pylint
    fn_list = ' '.join(fn_list)

    # Launch pylint with the appropriate options
    (pylint_stdout, pylint_stderr) = lint.py_run(fn_list + ' ' + pylint_command, return_std=True)

    # Extract the actual messages
    msgs = pylint_stdout.getvalue()

    # fpavogt, 2020-12-09: let's check the error messages, in case something went very wrong ...
    err_msgs = pylint_stderr.getvalue()
    if err_msgs != '':
        print('pylint stdout:')
        print(msgs)
        print('pylint stderr:')
        print(err_msgs)

        raise Exception('The linting crashed ?!')

    # Extract the score ...
    score = re.search(r'\s([\+\-\d\.]+)/10', msgs)[1]
    # ... and turn it into a float
    score = round(float(score), 2)

    # For the Github Action, raise an exception in case I get any restricted errors.
    if args.restrict is not None and score < 10:
        # Display the output, so we can learn something from it if needed
        print(msgs)
        raise Exception('Some forbidden pylint error codes are present!')

    # If I do not have any restricted errors, then simply show the pylint errors without failing.
    print(msgs)

    # If a minimum score was set, raise an Exception if it is not met, so that it can be picked-up
    # by a Github Action.
    if args.min_score is not None:
        if score < args.min_score:
            raise Exception('''pylint final score of %.2f is smaller than the specified
                               threshold of %.2f !''' % (float(score), args.min_score))


if __name__ == '__main__':

    main()
