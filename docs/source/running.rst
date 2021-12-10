.. include:: ./substitutions.rst

.. _using:

Using ampycloud
=================

.. _running:

Running the algorithm
---------------------

Applying the ampycloud algorithm to a given set of ceilometer cloud base hits is done via the following
function, that is also directly accessible as ``ampycloud.run()``:

.. autofunction:: ampycloud.core.run
    :noindex:


The following two functions, also accessible as ``ampycloud.metar() and ampycloud.synop()``,
will directly provide interested users with the ampycloud-METAR/synop messages for a given dataset:

.. autofunction:: ampycloud.core.metar
    :noindex:

.. autofunction:: ampycloud.core.synop
    :noindex:


.. _plotting:

Plotting the diagnostic diagram
-------------------------------

Users interested to plot the ampycloud diagnostic diagram can do using the following function,
which is also accessible as ``ampycloud.plots.diagnostic()``:

.. autofunction:: ampycloud.plots.core.diagnostic
    :noindex:
