
.. include:: ./substitutions.rst

ampycloud |version| |stars| |watch| |doi|
=========================================
|copyright| |license|
|pypi| |last-commit| |issues| |pytest-weekly|

.. _fig-demo:
.. figure:: ./examples/ampycloud_canonical_mock_demo.png
    :width: 750px
    :align: center
    :alt: ampycloud demo diagnostic diagram

    The ampycloud diagnostic diagram for its canonical mock dataset.

Welcome to the ampycloud documentation
--------------------------------------

* **What:** ampycloud refers to both a **Python package** and the **algorithm** at its core, designed
  to characterize cloud layers (i.e. height and sky coverage fraction) using ceilometer measurements
  (i.e. automatic cloud base *hits*), and derive a corresponding METAR-like message.
  A visual illustration of the algorithm is visible in :numref:`fig-demo`.

* **Where:** ampycloud lives in `a dedicated repository <https://github.com/MeteoSwiss/ampycloud>`_
  under the `MeteoSwiss organization <https://github.com/MeteoSwiss>`_ on Github, where you can
  submit all your `questions <https://github.com/MeteoSwiss/ampycloud/discussions>`_ and
  `bug reports <https://github.com/MeteoSwiss/ampycloud/issues>`_. See
  :ref:`troubleshooting:Troubleshooting` for more details.

* **Who:** ampycloud is being developed at `MeteoSwiss <https://www.meteoswiss.admin.ch>`__.
  See also the code's :ref:`license & copyright <license:License & Copyright>` information.

* **How:** a scientific article describing the ampycloud **algorithm** is currently in preparation.
  This article will be complemented by these webpages, that contain the official documentation of
  the ampycloud **Python package**.

Scope of ampycloud
------------------

.. important::
    .. include:: ./scope.rst


Table of contents
-----------------

.. toctree::
    :maxdepth: 2

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
