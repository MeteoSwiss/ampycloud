.. include:: ./substitutions.rst

.. _install:

Installation
============

.. todo::

    Include a link to the pypi page in the very next sentence.

ampycloud may, one day, be available on pypi, which should make its installation straightforward.
In a terminal, you would be able to type:

.. code-block:: python

    pip install ampycloud

And that would take care of things. ampycloud uses `semantic versioning <https://semver.org/>`_.
The latest stable version is |version|.

The most recent release of ampycloud is available for download/cloning from its
`Github repository <https://github.com/MeteoSwiss/ampycloud/releases/latest/>`_, in which case
the install command becomes:

.. code-block:: python

    cd ./where/you/stored/ampycloud/
    pip install -e .

Requirements
------------
ampycloud is compatible with the following python versions:

.. literalinclude:: ../../setup.py
    :language: python
    :lines: 39

Furthermore, ampycloud relies on a few external modules, which will be automatically installed by
``pip`` if required:

.. literalinclude:: ../../setup.py
    :language: python
    :lines: 41-46

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
