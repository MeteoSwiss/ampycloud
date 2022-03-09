"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: dynamic (scientific) parameters, which can be altered during execution.
"""

# Import from Python
from pathlib import Path
from ruamel.yaml import YAML


def get_default_prms() -> dict:
    """ Extract the default ampycloud parameters from the YAML configuration file. """

    yaml = YAML(typ='safe')
    out = yaml.load(Path(__file__).parent / 'prms' / 'ampycloud_default_prms.yml')

    return out


#: dict: The ampycloud parameters, first set from a config file via :py:func:`.get_default_prms`
AMPYCLOUD_PRMS = get_default_prms()
