.. include:: ./substitutions.rst

.. _install:

Installation
============

ampycloud is available on pypi, which should make its installation straightforward.
Typing the following in a terminal should take care of things:

.. code-block:: python

    pip install ampycloud

ampycloud uses `semantic versioning <https://semver.org/>`_. The latest stable version is |version|.

The different releases of ampycloud are also available for download from its
`Github repository <https://github.com/MeteoSwiss/ampycloud/releases/latest/>`_.

If you plan to do dev-work with ampycloud, you should instead clone/fork the `develop` branch
`of the ampycloud Github repository <https://github.com/MeteoSwiss/ampycloud/tree/develop>`__, in
which case the install command becomes:

.. code-block:: python

    cd ./where/you/forked/ampycloud/
    pip install -e .[dev]

.. note::
    If you plan to do dev-work with ampycloud, you ought to read the
    `contributing guidelines <https://github.com/MeteoSwiss/ampycloud/blob/develop/CONTRIBUTING.md>`__
    first.

Requirements
------------
ampycloud is compatible with the following python versions:

.. literalinclude:: ../../setup.py
    :language: python
    :lines: 43

Furthermore, ampycloud relies on a few external modules, which will be automatically installed by
``pip`` if required:

.. literalinclude:: ../../setup.py
    :language: python
    :lines: 44-53

Testing the installation & Speed benchmark
------------------------------------------

ampycloud is shipped with a high-level entry point that allows to run a speed check from the
command line. To see if your installation was successful, the command ``ampycloud_speed_test -h``
should return:

.. literalinclude:: ampycloud_speed_test_help_msg.txt
    :language: none

To actually run the speed test, simply call ``ampycloud_speed_test``, optionally setting a different
number of executions via the ``-niter`` argument. For comparison purposes, here are the performances
on the machine that was responsible for compiling this documentation:

.. literalinclude:: ampycloud_speed_test_msg.txt
    :language: none
