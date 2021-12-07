"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: highest-level init magic
"""

# Import from Python
import logging
from pathlib import Path
from matplotlib import pyplot as plt

# Import from this package
from . import version as vers

# Instantiate the module logger
logger = logging.getLogger(__name__)
# Hide any log messages if the user did not instantiate any handler
# This is the only place where I'll be doing this in ampycloud
# For details, see: https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logger.addHandler(logging.NullHandler())

# Make the package version easily accessible, with the usual format
__version__ = vers.VERSION

# Make sure the base plotting style is used at the very least
# Should this be a warning ?
logger.info('Setting the base (custom) matplotlib style for ampycloud.')
plt.style.use(str(Path(__file__).parent / 'plots'/ 'mpl_styles' / 'base.mplstyle'))