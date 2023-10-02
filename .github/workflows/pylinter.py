# -*- coding: utf-8 -*-
'''
Copyright (c) 2020-2023 MeteoSwiss, created by F.P.A. Vogt; frederic.vogt@meteoswiss.ch

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

This script can be used together with a Github Action to run pylint on all the .py files in a
repository. Command line arguments can be used to search for a specific subset of errors (if any are
found, this script will raise an Exception), or to ignore some errors in a generic search (which
will print all the errors found, but will not raise any Exception). If a score is specified, the
script will raise an Exception if it is not met.

Created May 2020; fpavogt; frederic.vogt@meteoswiss.ch
Adapted Jan 2022; fpavogt; frederic.vogt@meteoswiss.ch
Updated Jul 2023; fpavogt; frederic.vogt@meteoswiss.ch
'''

import argparse
import glob
import os
from pylint import lint


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
        pylint_args = ['--disable=all', '--enable=' + error_codes]

    # or do I rather want to simply exclude some errors ?
    elif args.exclude is not None:
        error_codes = ','.join(args.exclude)
        pylint_args = ['--disable=' + error_codes]

    else:  # just run pylint without tweaks

        pylint_args = []

    # Get a list of all the .py files here and in all the subfolders.
    fn_list = glob.glob(os.path.join('.', '**', '*.py'), recursive=True)

    # Skip the docs and build folders
    for bad_item in [os.path.join('.', 'build'), os.path.join('.', 'docs')]:
        fn_list = [item for item in fn_list if bad_item not in item]

    # Launch pylint with the appropriate options
    run = lint.Run(pylint_args + fn_list, do_exit=False)
    # Collect the total score
    score = run.linter.stats.global_note

    # Raise an exception in case I get any restricted errors.
    if args.restrict is not None and score < 10:
        raise RuntimeError('Some forbidden pylint error codes are present!')

    # If a minimum score was set, raise an Exception if it is not met, so that it can be picked-up
    # by a Github Action.
    if args.min_score is not None:
        if score < args.min_score:
            raise RuntimeError(f'pylint final score of {score:.2f} is smaller than' +
                               ' the specified threshold of {args.min_score:.2f} !')


if __name__ == '__main__':

    main()
