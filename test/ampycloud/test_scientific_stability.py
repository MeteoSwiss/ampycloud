"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the scientific stability of the package
"""

# Import from Python
from pathlib import Path
import pickle
import pytest
import pandas as pd

# Import from ampycloud
import ampycloud
from ampycloud import dynamic, reset_prms
from ampycloud.plots import diagnostic


def get_cases():
    """ Utility function that extracts a list of scientific cases (i.e. ref data files) to assess.

    Fixes #85 by feeding the result to pytest.mark.parametrize().

    """

    # Where is the data located, and how many cases do I have ?
    ref_data_path = Path(__file__).parent / 'ref_data'
    return sorted(ref_data_path.glob('*.pkl'))


@pytest.mark.parametrize("ref_data_file", get_cases())
def test_scientific_stability(mpls: str, do_sciplots: bool, ref_data_file: Path) -> None:
    """ Test the scientific stability of ampycloud. A specific cases is being processed,
    and the resulting METAR are compared with the expected outcome.

    Args:
        mpls (str): False, or the value of MPL_STYLE requested by the user. This is set
            automatically by a fixture that fetches the corresponding command line argument.
            See conftest.py for details.
        do_sciplots (bool): True to make plots. This is set automatically
            by a fixture that fetches the corresponding command line argument.
            See conftest.py for details.
        ref_data_file (Path): path+filename to the pickled test data.

    Important:
        We assess the scientific stability using only the METAR messages. This implies that any
        changes to the slicing/grouping/clustering will NOT be caught by this test if they have no
        impact on the resulting METAR message.

        This is intended. The point is to have enough representative/special/tricky/interesting
        reference cases to catch any **significant** changes in the code behavior.

    """

    # Extract the reference data
    with open(ref_data_file, 'rb') as f:
        data = pickle.load(f)

    # Fix the dtype of the ceilo column
    data['ceilo'] = data.loc[:, 'ceilo'].astype(pd.StringDtype())

    # Get other useful info
    geoloc = ref_data_file.stem.split('_')[0]
    ref_dt = ref_data_file.stem.split('_')[1].replace('-', ' ')
    ref_metar = ref_data_file.stem.split('_')[2].split('.')[0].replace('-', ' ')

    # Do I need to set a specific MSA ?
    if 'MSA' in ref_data_file.stem:
        dynamic.AMPYCLOUD_PRMS['MSA'] = int(ref_data_file.stem.split('_')[3].split('.')[0][3:])
    else:
        # Make sure I use the default MSA
        reset_prms()

    # Run ampycloud
    chunk = ampycloud.run(data, geoloc=geoloc, ref_dt=ref_dt)

    # Should I make a plot ?
    if do_sciplots:
        # Do I need to set a specific plotting style ?
        if mpls:
            dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] = mpls
        # Create the plot
        diagnostic(chunk, upto='layers', ref_metar=ref_metar, ref_metar_origin='Should be',
                   show=False, save_stem=ref_data_file.stem, save_fmts=['png', 'pdf'])

    # Was the computed METAR as expected ?
    assert chunk.metar_msg() == ref_metar

    # Reset the ampycloud parameters to avoid wreaking havoc with the other tests
    reset_prms()
