"""
Copyright (c) 2021-2022 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: custom error and warning classes
"""


class AmpycloudError(Exception):
    """ The default error class for ampycloud, which is a child of the :py:exc:`Exception` class.
    """


class AmpycloudWarning(Warning):
    """ The default warning class for ampycloud, which is a child of the :py:class:`Warning` class.
    """
