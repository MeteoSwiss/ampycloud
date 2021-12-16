.. include:: ./substitutions.rst

.. _using:

Using ampycloud
=================

.. _running:

Running the algorithm
---------------------

Applying the ampycloud algorithm to a given set of ceilometer cloud base hits is done via the
following function, that is also directly accessible as ``ampycloud.run()``.

.. autofunction:: ampycloud.core.run
    :noindex:


The following two functions, also accessible as ``ampycloud.metar() and ampycloud.synop()``,
will directly provide interested users with the ampycloud-METAR/synop messages for a given dataset.

.. autofunction:: ampycloud.core.metar
    :noindex:

.. autofunction:: ampycloud.core.synop
    :noindex:


Adjusting the default algorithm parameters
..........................................

The ampycloud parameters with a **scientific** impact on the outcome of the algorithm are accessible
in the `ampycloud.dynamic` module.  From there, users can easily adjust them as they see fit. For
example:
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
