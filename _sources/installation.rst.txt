.. include:: ./substitutions.rst

.. _install:

Installation
============

End users / Install from PyPI
------------------------------
ampycloud is available on PyPI, which should make its installation straightforward.
Typing the following in a terminal should take care of things:

.. code-block:: python

    pip install ampycloud

ampycloud uses `semantic versioning <https://semver.org/>`_. The latest stable version is |version|.

The different releases of ampycloud are also available for download from its
`Github repository <https://github.com/MeteoSwiss/ampycloud/releases/latest/>`_.

or (if you prefer Poetry):

.. code-block:: python

    poetry add ampycloud

Development setup (Poetry)
--------------------------
If you plan to contribute or run the test suite, use the Poetry-based development workflow.
And clone/fork the `main` branch `of the ampycloud Github repository <https://github.com/MeteoSwiss/ampycloud/tree/main>`__, in
which case the install command becomes:

.. code-block:: python

    # clone the project and enter the repo
    git clone https://github.com/MeteoSwiss/ampycloud.git
    cd ampycloud

    # create/install the development environment
    poetry install

    # run test suite
    poetry run pytest

    # run the quality tools
    poetry run pylint ampycloud
    poetry run mypy ampycloud
    poetry run ruff format --check

.. note::
    If you do not use Poetry, the editable pip install is an alternative to develop locally:

    .. code-block:: python

        python -m pip install -e '.[dev]'

.. note::
    If you plan to do dev-work with ampycloud, you ought to read the
    `contributing guidelines <https://github.com/MeteoSwiss/ampycloud/blob/develop/CONTRIBUTING.md>`__
    first.

Requirements
------------
ampycloud is compatible with the following python versions:

.. literalinclude:: ../pyproject.toml
    :language: toml
    :start-at: requires-python
    :end-at: requires-python

Furthermore, ampycloud relies on a few external modules, which will be automatically installed by
``pip``/``poetry`` if required:

.. literalinclude:: ../pyproject.toml
    :language: toml
    :start-at: dependencies = [
    :end-at: ]

Testing the installation & Speed benchmark
------------------------------------------

ampycloud is shipped with a high-level entry point that allows to run a speed check from the
command line. To see if your installation was successful, run the following command:

.. code-block:: none

    ampycloud_speed_test -h

To actually run the speed test, simply call ``ampycloud_speed_test``, optionally setting a different
number of executions via the ``-niter`` argument. The dedicated ``CI_speed_check`` workflow tracks
these performances over time to catch any regression.
