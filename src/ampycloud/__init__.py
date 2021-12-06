"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: highest-level init magic
"""

from pathlib import Path
from matplotlib import pyplot as plt

# Import the necessary stuff
from . import version as vers

# Make the package versionb easily accessible, with the usual format
__version__ = vers.VERSION

# Make sure the base plotting style is used at the very least
plt.style.use(str(Path(__file__).parent / 'plots'/ 'mpl_styles' / 'base.mplstyle'))
