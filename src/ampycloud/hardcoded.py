"""
Copyright (c) 2022-2024 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: hardcoded data
"""

from pandas import StringDtype

#: dict: the columns & associated types required for the pandas DataFrame fed to ampycloud.
REQ_DATA_COLS = {'ceilo': StringDtype(), 'dt': float, 'height': float, 'type': int}
