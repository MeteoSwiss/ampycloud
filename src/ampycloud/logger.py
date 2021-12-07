"""
Copyright (c) 2021 MeteoSwiss, contributors listed in AUTHORS.

Distributed under the terms of the 3-Clause BSD License.

SPDX-License-Identifier: BSD-3-Clause

Module contains: logging utilities
"""

# Import from Python
import inspect
from functools import wraps

def log_func_call(logger):
    """ Intended as a decorator to log function calls.

    The first part of the message containing the function name is at the 'INFO' level.
    The second part of the message containing the argument values is at the 'DEBUG' level.

    Args:
        logger (logging.logger): a logger to feed info to.

    Note:
        Adapted from the similar dvas function, which itself was adapted from
        `this post <https://stackoverflow.com/questions/218616>`__ on SO,
        in particular the reply from Kfir Eisner and Peter Mortensen.
        See also `this <https://docs.python.org/3/library/inspect.html#inspect.BoundArguments>`__.

    """

    def deco(func):
        """ This is the actual function decorator. """

        @wraps(func)  # This black magic is required for Sphinx to still pickup the func docstrings.
        def inner_deco(*args, **kwargs):
            """ The core function, where the magic happens. """

            # Extract all the arguments and named-arguments fed to the function.
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Assemble a log message witht he function name ...
            log_msg = ' Executing %s() ...' % (func.__name__)
            # ... and log it at the INFO level.
            logger.info(log_msg)

            # Then get extra information about the arguments ...
            log_msg = ' ... with the following input: %s' % (str(dict(bound_args.arguments)))
            # ... and log it at the DEBUG level.
            logger.debug(log_msg)

            # Launch the actual function
            out = func(*args, **kwargs)
            return out
        return inner_deco
    return deco
