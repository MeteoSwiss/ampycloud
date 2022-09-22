from datetime import datetime
import ampycloud
from ampycloud.utils import mocker
from ampycloud.plots import diagnostic
import sys

# Generate the demo dataset for ampycloud to test the minimum separation parameter.
# Your data should have *exactly* this structure

## EXAMPLE 1
n_ceilos = 4
lookback_time = 1200
rate = 30
mock_data = mocker.mock_layers(n_ceilos, lookback_time, rate,
                                   [{'alt': 500, 'alt_std': 30, 'sky_cov_frac': 0.5,
                                     'period': 100, 'amplitude': 20},
                                     {'alt': 700, 'alt_std': 30, 'sky_cov_frac': 0.5,
                                     'period': 100, 'amplitude': 20},
                                     {'alt': 1400, 'alt_std': 30, 'sky_cov_frac': 0.5,
                                     'period': 100, 'amplitude': 20},
                                     {'alt': 1600, 'alt_std': 30, 'sky_cov_frac': 0.5,
                                     'period': 100, 'amplitude': 20}])

# Run the ampycloud algorithm on it, setting the MSA to 10'000 ft
chunk = ampycloud.run(mock_data, geoloc='Mock data', ref_dt=datetime.now())

# Get the resulting METAR message
print(chunk.metar_msg())

# Display the full information available for the layers found
print(chunk.layers)

# And for the most motivated, plot the diagnostic diagram
diagnostic(chunk, upto='layers', show=True, save_stem='ampycloud_demo_minsep', save_fmts=['png'])