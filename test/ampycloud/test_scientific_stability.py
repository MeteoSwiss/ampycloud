"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module content: tests for the scientific stability of the package
"""

# Import from Python
from pathlib import Path
import pickle

# Import from ampycloud
import ampycloud
from ampycloud import dynamic, reset_prms
from ampycloud.plots import diagnostic

def test_scientific_stability(mpls, do_sciplots):
    """ Test the scientific stability of ampycloud. A series of reference cases is being processed,
    and the resulting METAR are compared with the expected outcome.

    Args:
        mpls: False, or the value of MPL_STYLE requested by the user. This is set automatically
            by a fixture that fetches the corresponding command line argument.
            See conftest.py for details.
        do_sciplots: True to make plots. This is set automatically
            by a fixture that fetches the corresponding command line argument.
            See conftest.py for details.

    Important:
        We assess the scientific stability using METAR only. This implies that any changes to the
        slicing/grouping/clustering will NOT be caught by this test if they have no impact on the
        resulting METAR.

        This is intended. The point is to have enough representative/special/tricky/interesting
        reference cases to catch any **significant** changes in the code behavior.

    """

    # Where it the data located, and how many cases do I have
    ref_data_path = Path(__file__).parent / 'ref_data'
    ref_data_files = ref_data_path.glob('*.pkl')

    # Start processing every file
    for ref_data_file in ref_data_files:

        # Extract the reference data
        with open(ref_data_file, 'rb') as f:
            data = pickle.load(f)

        # Get other useful info
        geoloc = ref_data_file.stem.split('_')[0]
        ref_dt = ref_data_file.stem.split('_')[1].replace('-', ' ')
        ref_metar = ref_data_file.stem.split('_')[2].split('.')[0].replace('-', ' ')

        if 'MSA' in ref_data_file.stem:

            dynamic.AMPYCLOUD_PRMS.MSA = int(ref_data_file.setm.split('_')[3].split('.')[0][3:])

        else:
            # Use the default MSA
            reset_prms()

        # Run ampycloud
        chunk = ampycloud.run(data, geoloc=geoloc, ref_dt=ref_dt)

        if do_sciplots:

            if mpls:
                dynamic.AMPYCLOUD_PRMS.MPL_STYLE = mpls

            # Create the plot
            diagnostic(chunk, upto='layers', ref_metar=ref_metar, ref_metar_origin='Should be',
                       show=False, save_stem=ref_data_file.stem, save_fmts=['pdf'])

        assert chunk.metar_msg() == ref_metar

    # Reset the ampyclou parameters to avoid wreaking havoc with the other tests
    reset_prms()
