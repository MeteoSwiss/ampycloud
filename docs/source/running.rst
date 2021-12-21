.. include:: ./substitutions.rst

.. _using:

Using ampycloud
=================

.. _running:

Running the algorithm
---------------------

ampycloud.core.run
..................

Applying the ampycloud algorithm to a given set of ceilometer cloud base hits is done via the
following function, that is also directly accessible as ``ampycloud.run()``.

.. autofunction:: ampycloud.core.run
    :noindex:


The no-plots-required shortcuts
...............................

The following two functions, also accessible as ``ampycloud.metar() and ampycloud.synop()``,
will directly provide interested users with the ampycloud-METAR/synop messages for a given dataset.

.. autofunction:: ampycloud.core.metar
    :noindex:

.. autofunction:: ampycloud.core.synop
    :noindex:


Adjusting the default algorithm parameters
..........................................

.. caution::

    It is highly recommended to adjust any scientific parameters **before** executing any of the
    ampycloud routines. Doing otherwise may have un-expected consequences. You have been warned.

The ampycloud parameters with a **scientific** impact on the outcome of the algorithm
(see :ref:`here for the complete list <parameters:The ampycloud scientific parameters>`)
are accessible in the `ampycloud.dynamic` module.  From there, users can easily adjust them as they
see fit. For example:
::

    from ampycloud import dynamic

    dynamic.AMPYCLOUD_PRMS.OKTA_LIM8 = 95

Note that it is important to always import the entire `dynamic` module and stick to the above
structure if the updated parameters are to be *seen* by all the ampycloud modules.

Alternatively, all the scientific parameters can be adjusted and fed to ampycloud via a YAML file,
in which case the routines ```ampycloud.copy_prm_file()`` and ``ampycloud.set_prms()`` may be of
interest.

.. autofunction:: ampycloud.core.copy_prm_file
    :noindex:


.. autofunction:: ampycloud.core.set_prms
    :noindex:


If all hope is lost and you wish to revert to the original (default) values of the all the
ampycloud scientific parameters, you can use ```ampycloud.reset_prms()``.

.. autofunction:: ampycloud.core.reset_prms
    :noindex:


Advanced info for advanced users
********************************

The majority of parameters present in ``dynamic.AMPYCLOUD_PRMS`` are fetched directly by the
methods of the ``CeiloChunk`` class when they are called. As a result, modifying a specific
parameter in ``dynamic.AMPYCLOUD_PRMS`` (e.g. ``dynamic.AMPYCLOUD_PRMS.OKTA_LIM8``) will be seen
by any ``CeiloChunk`` instance already in existence.

The ``MSA`` and ``MSA_HIT_BUFFER`` are the only exception to this rule ! These two
parameters are being applied (and deep-copied as ``CeiloChunk`` class variables) immediately at the
initialization of any ``CeiloChunk`` instance. This implies that:

    1. any cloud hits above ``MSA + MSA_HIT_BUFFER`` in the data will be cropped immediately in the
       ``CeiloChunk.__init__()`` routine, and thus cannot be recovered by subsequently changing the
       value of ``dynamic.AMPYCLOUD_PRMS.MSA``, and
    2. any METAR/SYNOP message issued will always be subject to the Minimum Sector Altitude
       value that was specified in ``dynamic.AMPYCLOUD_PRMS.MSA`` at the time the class
       instance was initialized. This is to ensure consistency with the cropped data at all times.

.. _logging:

Logging
-------

A ``NullHandler()`` is being set by ampycloud, such that no logging will be apparent to the users
unless they explicitly set it up
(`see here <https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library>`_ for
more details).

As an example, to enable ampycloud log messages all the way down to the ``DEBUG`` level, users can
make the following call before running ampycloud functions:
::

    import logging

    logging.basicConfig()
    logging.getLogger('ampycloud').setLevel('DEBUG')


Each ampycloud module has a dedicated ``logger`` based on the module ``__name__``. Hence, users
can adjust the logging level of each ampycloud module however they desire, e.g.:
::

    logging.getLogger('ampycloud.wmo').setLevel('WARNING')
    logging.getLogger('ampycloud.scaler').setLevel('DEBUG')

.. _plotting:

Plotting the diagnostic diagram
-------------------------------

Users interested to plot the ampycloud diagnostic diagram can do using the following function,
which is also accessible as ``ampycloud.plots.diagnostic()``:

.. autofunction:: ampycloud.plots.core.diagnostic
    :noindex:


Adjusting the plotting style
............................
ampycloud ships with its own set of matplotlib style files, that are used in `context`, and thus
will not impact any user-specified setups.

Whereas the default parameters should ensure a decent-enough look for the diagnostic diagrams of
ampycloud, a better look can be achieved by using a system-wide LaTeX installation. Provided this is
available, users interested in creating nicer-looking diagnostic diagrams can do so by setting
the appropriate ampycloud parameter:
::

    from ampycloud import dynamic
    dynamic.AMPYCLOUD_PRMS.MPL_STYLE = 'latex'

And for the most demanding users that want nothing but the best, they can create plots with actual
okta symbols if they install the `metsymb LaTeX package <https://github.com/MeteoSwiss/metsymb>`__
system-wide, and set:
::

    from ampycloud import dynamic
    dynamic.AMPYCLOUD_PRMS.MPL_STYLE = 'metsymb'


.. warning::

    Using a system-wide LaTeX installation to create matplotlib figures **is not officially
    supported by matplotib**, and thus **not officially supported by the ampycloud** either.
