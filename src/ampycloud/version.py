"""
Copyright (c) 2021-2026 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: ampycloud version
"""
#import ampycloud
#:str: the one-and-only place where the ampycloud version is set.
#VERSION = ampycloud.__version__
#VERSION = "2.2.0"

from importlib.metadata import version, PackageNotFoundError

try:
    VERSION = version("ampycloud")
except PackageNotFoundError:
    # Package is not installed (e.g., during development)
    # Use a development version that is greater than "0"
    VERSION = "0.0.0"
