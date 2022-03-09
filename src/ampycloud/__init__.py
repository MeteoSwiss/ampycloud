"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: highest-level init magic
"""

# Import from Python
import logging

# Import from this package
from . import version as vers
from .core import *  # Bring out the core routines for easy access by the user

# Instantiate the module logger
logger = logging.getLogger(__name__)
# Hide any log messages if the user did not instantiate any handler
# This is the only place where I'll be doing this in ampycloud
# For details, see: https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logger.addHandler(logging.NullHandler())

# Make the package version easily accessible, with the usual format
__version__ = vers.VERSION
