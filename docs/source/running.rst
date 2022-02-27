.. include:: ./substitutions.rst

.. _using:

Using ampycloud
=================

A no-words example for those that want to get started quickly
-------------------------------------------------------------

::

    from datetime import datetime
    import ampycloud
    from ampycloud.utils import mocker
    from ampycloud.plots import diagnostic

    # Generate the canonical demo dataset for ampycloud
    # Your data should have *exactly* this structure
    mock_data = mocker.canonical_demo_data()

    # Run the ampycloud algorithm on it, setting the MSA to 10'000 ft
    chunk = ampycloud.run(mock_data, prms={'MSA': 10000},
                          geoloc='Mock data', ref_dt=datetime.now())

    # Get the resulting METAR message
    print(chunk.metar_msg())

    # Display the full information available for the layers found
    print(chunk.layers)

    # And for the most motivated, plot the diagnostic diagram
    diagnostic(chunk, upto='layers', show=True, save_stem='ampycloud_demo')


The input data
--------------

The ampycloud algorithm is meant to process cloud base *hits* from ceilometer observations. A given
set of hits to be processed by the ampycloud package must be stored inside a
:py:class:`pandas.DataFrame` with a specific set of characteristics outlined below. Users can use
the following utility function to check whether a given :py:class:`pandas.DataFrame` meets all the
requirements of ampycloud.

.. autofunction:: ampycloud.utils.utils.check_data_consistency
    :noindex:

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

The following function, also accessible as ``ampycloud.metar()``,
will directly provide interested users with the ampycloud METAR-like message for a given dataset.
It is a convenience function intended for users that do not want to generate diagnostic plots, but
only seek the outcome of the ampycloud algorithm formatted as a METAR-like ``str``.

.. autofunction:: ampycloud.core.metar
    :noindex:

Adjusting the default algorithm parameters
..........................................

The ampycloud parameters with a **scientific** impact on the outcome of the algorithm
(see :ref:`here for the complete list <parameters:The ampycloud scientific parameters>`)
are accessible via :py:data:`ampycloud.dynamic.AMPYCLOUD_PRMS` as a nested dictionnary. When a new
:py:class:`ampycloud.data.CeiloChunk` instance is being initiated, a copy of this nested dictionary
is being stored as an instance variable (possibly adjusting specific parameters via the ``prms``
keyword argument).

There are thus 2+1 ways to adjust the ampycloud scientific parameters:

    * **1.a: Adjust them globally** in :py:data:`ampycloud.dynamic.AMPYCOUD_PRMS`, like so:
      ::

          from ampycloud import dynamic

          dynamic.AMPYCLOUD_PRMS['OKTA_LIM8'] = 95


      .. important::

          Always import the entire :py:mod:`ampycloud.dynamic` module and stick to the
          above example structure, if the updated parameters are to be *seen* by all the ampycloud
          modules.


    * **1.b: Adjust them globally** via a YAML file, and :py:func:`ampycloud.core.set_prms`. With
      this approach, :py:func:`ampycloud.core.copy_prm_file()` can be used to obtain a local
      copy of the default ampycloud parameters.


    * **2: Adjust them for locally** for every execution of ampycloud by feeding a suitable nested
      dictionary to :py:func:`ampycloud.core.run`. The dictionnary, the keys and levels of which
      should be consistent with :py:data:`ampycloud.dynamic.AMPYCLOUD_PRMS`, only need to contains
      the specific parameters that one requires to be different from the default values.
      ::

          # Define only the parameters that are non-default. To adjust the MSA, use:
          my_prms = {'MSA': 10000}

          # Or to adjust both the MSA and some other algorithm parameter:
          my_prms = {'MSA': 10000, 'GROUPING_PRMS':{'dt_scale_kwargs':{'scale': 300}}}

          # Then feed them directly to the run call
          chunk = ampycloud.run(some_data_tbd, prms=my_prms)


.. warning::

    Options 1a and 1b are **not** thread-safe. Users planning to launch multiple ampycloud
    processes simultaneously are urged to use option 2, if they need to set distinct parameters
    between each. In case of doubts, the parameters used by a given
    :py:class:`ampycloud.data.CeiloChunk` instance is accessible via the (parent)
    :py:meth:`ampycloud.data.AbstractChunk.prms` property.


If all hope is lost and you wish to revert to the original (default) values of all the
ampycloud scientific parameters, you can use :py:func:`ampycloud.core.reset_prms()`.

.. autofunction:: ampycloud.core.reset_prms
    :noindex:

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
    dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] = 'latex'

And for the most demanding users that want nothing but the best, they can create plots with actual
okta symbols if they install the `metsymb LaTeX package <https://github.com/MeteoSwiss/metsymb>`__
system-wide, and set:
::

    from ampycloud import dynamic
    dynamic.AMPYCLOUD_PRMS['MPL_STYLE'] = 'metsymb'


.. important::

    Using a system-wide LaTeX installation to create matplotlib figures **is not officially
    supported by matplotib**, and thus **not officially supported by ampycloud** either.
