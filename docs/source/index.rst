
.. include:: ./substitutions.rst

ampycloud |version| |stars| |watch|
===================================

|copyright| |license| |github| |pypi| |last-commit| |issues|

.. todo::

    Tags for the latest pypi release and associated DOI should be added when releasing the code
    for the first time. These should also be added to the :ref:`acknowledge:Acknowledging ampycloud`
    page.

.. _fig-demo:
.. figure:: ./examples/ampycloud_canonical_mock_demo.png
    :width: 750px
    :align: center
    :alt: ampycloud demo diagnostic diagram

    *Figure 1: the ampycloud diagnostic diagram for its canonical mock dataset.*

**Welcome to the ampycloud documentation !**

**WHAT:** ampycloud refers to both a Python package and the algorithm at its core, designed to
characterize cloud layers (i.e. height and sky coverage fraction) using ceilometer measurements
(i.e. automatic cloud base *hits* measurements), and derive the corresponding METAR-like message.
A visual illustration of the algorithm is visible in :numref:`fig-demo`, which corresponds to the
*ampycloud diagnostic diagram* for the ampycloud canonical mock dataset.

**WHERE:** ampycloud lives in `a dedicated repository <https://github.com/MeteoSwiss/ampycloud>`_
under the `MeteoSwiss organization <https://github.com/MeteoSwiss>`_ on Github, where you can
submit all your `questions <https://github.com/MeteoSwiss/ampycloud/discussions>`_ and
`bug reports <https://github.com/MeteoSwiss/ampycloud/issues>`_. See
:ref:`troubleshooting:Troubleshooting` for more details.

**WHO:** ampycloud is being developped at MeteoSwiss, with contributions from the following
`authors. <https://github.com/MeteoSwiss/ampycloud/blob/develop/AUTHORS>`_ See also the code's
:ref:`license & copyright <license:License & Copyright>` information.

.. important::

    ampycloud is a key dependency of the automatic METAR-generating code of MeteoSwiss,
    which requires all its dependencies to be robust and stable.

    This has the following implications for ampycloud:

        * The scope of ampycloud will remain limited to the **automatic processing of ceilometer
          hits**.
        * ampycloud can evidently be used for R&D work, but the code itself should not be
          seen as an R&D platform.
        * Contributions via Pull Requests are always welcome (and appreciated !), but will only be
          considered if they:

            - remove a bug, or
            - improve the usability of ampycloud without altering the quality of the results, or
            - demonstrate a significant improvement in the quality of the results.

        * The ingestion of external contributions may be delayed to allow for careful, internal
          verification that they do not affect the MeteoSwiss operational chain that relies on
          ampycloud.


**Table of contents:**

.. toctree::
    :maxdepth: 1

    Home <self>
    installation
    running
    parameters
    troubleshooting
    acknowledge
    license
    changelog
    Contributing <https://github.com/MeteoSwiss/ampycloud/blob/develop/CONTRIBUTING.md>
    Github repository <https://github.com/MeteoSwiss/ampycloud>
    modules
    doc_todo