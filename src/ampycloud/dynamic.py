"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: dynamic (scientific) parameters, which can be altered during execution.
"""

# Import from Python
from pathlib import Path
from yaconfigobject import Config

def get_default_prms() -> Config:
    """ Extract the default ampycloud parameters from the YAML configuration file. """

    return Config(paths=[str(Path(__file__).parent/ 'prms')], name='ampycloud_default_prms.yml')


#:dict: The ampycloud parameters, first set from a config file via :py:func:`.get_default_prms`
AMPYCLOUD_PRMS = get_default_prms()
