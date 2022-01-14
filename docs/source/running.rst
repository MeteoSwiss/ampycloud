.. include:: ./substitutions.rst

.. _using:

Using ampycloud
=================

.. _running:

Running the algorithm
---------------------

The :py:func:`ampycloud.core.run` function
..........................................

Applying the ampycloud algorithm to a given set of ceilometer cloud base hits is done via the
following function, that is also directly accessible as ``ampycloud.run()``.

.. autofunction:: ampycloud.core.run
    :noindex:

The :py:class:`ampycloud.data.CeiloChunk` class
...............................................

The function :py:func:`ampycloud.core.run` returns a :py:class:`ampycloud.data.CeiloChunk` class
instance, which is at the core of ampycloud. This class is used to load and format the
user-supplied data, execute the different ampycloud algorithm steps, and format their outcomes.

The properties of the slices/groups/layers identified by the different steps of the ampycloud
algorithm are accessible, as :py:class:`pandas.DataFrame` instances, via the class properties
:py:attr:`ampycloud.data.CeiloChunk.slices`, :py:attr:`ampycloud.data.CeiloChunk.groups`, and
:py:attr:`ampycloud.data.CeiloChunk.layers`.

.. note::
    :py:meth:`ampycloud.data.CeiloChunk.metar_msg` relies on
    :py:attr:`ampycloud.data.CeiloChunk.layers` to derive the corresponding METAR-like message.

All these slices/groups/layer parameters are being compiled/computed by
:py:meth:`ampycloud.data.CeiloChunk.metarize`, which contains all the info about the different
parameters.

.. autofunction:: ampycloud.data.CeiloChunk.metarize
    :noindex:


The no-plots-required shortcut
..............................

The following functions, also accessible as ``ampycloud.metar()``,
will directly provide interested users with the ampycloud METAR-like message for a given dataset.

.. autofunction:: ampycloud.core.metar
    :noindex:

Adjusting the default algorithm parameters
..........................................

.. important::

    It is highly recommended to adjust any scientific parameters **before** executing any of the
    ampycloud routines. Doing otherwise may have un-expected consequences (i.e. parameters may not
    have the expected value). You have been warned.

The ampycloud parameters with a **scientific** impact on the outcome of the algorithm
(see :ref:`here for the complete list <parameters:The ampycloud scientific parameters>`)
are accessible in the :py:mod:`ampycloud.dynamic` module.  From there, users can easily adjust them
as they see fit. For example:
::

    from ampycloud import dynamic

    dynamic.AMPYCLOUD_PRMS.OKTA_LIM8 = 95

Note that it is important to always import the entire :py:mod:`ampycloud.dynamic` module and stick to the
above structure if the updated parameters are to be *seen* by all the ampycloud modules.

Alternatively, all the scientific parameters can be adjusted and fed to ampycloud via a YAML file,
in which case the following routines, also accessible as ``ampycloud.copy_prm_file()`` and
``ampycloud.set_prms()``, may be of interest:

.. autofunction:: ampycloud.core.copy_prm_file
    :noindex:


.. autofunction:: ampycloud.core.set_prms
    :noindex:


If all hope is lost and you wish to revert to the original (default) values of all the
ampycloud scientific parameters, you can use :py:func:`ampycloud.core.reset_prms()`.

.. autofunction:: ampycloud.core.reset_prms
    :noindex:


Advanced info for advanced users
********************************

The majority of parameters present in :py:data:`ampycloud.dynamic.AMPYCLOUD_PRMS` are fetched
directly by the methods of the :py:class:`ampycloud.data.CeiloChunk` class when they are required.
As a result, modifying a specific entry in :py:data:`ampycloud.dynamic.AMPYCLOUD_PRMS` (e.g.
``OKTA_LIM8``) will be seen by any :py:class:`ampycloud.data.CeiloChunk` instance already in
existence.

The ``MSA`` and ``MSA_HIT_BUFFER`` entries are the only exception to this rule ! These two
parameters are being applied (and deep-copied as :py:class:`ampycloud.data.CeiloChunk` instance
attributes) immediately at the initialization of any :py:class:`ampycloud.data.CeiloChunk` instance.
This implies that:

    1. any cloud hits above ``MSA + MSA_HIT_BUFFER`` in the data will be cropped immediately in the
       :py:meth:`ampycloud.data.CeiloChunk.__init__` routine, and thus cannot be recovered by
       subsequently changing the value of ``MSA`` in :py:data:`ampycloud.dynamic.AMPYCLOUD_PRMS`,
       and
    2. any METAR-like message issued will always be subject to the Minimum Sector Altitude
       value that was specified in :py:data:`ampycloud.dynamic.AMPYCLOUD_PRMS` at the time the
       :py:class:`ampycloud.data.CeiloChunk` instance was initialized. This is to ensure
       consistency with the cropped data at all times.

.. _logging:

Logging
-------

A :py:class:`logging.NullHandler` instance is being created by ampycloud, such that no logging will
be apparent to the users unless they explicitly set it up themselves
(`see here <https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library>`_ for
more details).

As an example, to enable ampycloud log messages all the way down to the ``DEBUG`` level, users can
make the following call before running ampycloud functions:
::

    import logging

    logging.basicConfig()
    logging.getLogger('ampycloud').setLevel('DEBUG')


Each ampycloud module has a dedicated logger based on the module ``__name__``. Hence, users
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


.. important::

    Using a system-wide LaTeX installation to create matplotlib figures **is not officially
    supported by matplotib**, and thus **not officially supported by ampycloud** either.
