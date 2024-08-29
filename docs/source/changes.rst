.. include:: ./substitutions.rst

.. _install:

Scientific changes since v2.0.0
===============================

The scientific documentation of Ampycloud v2.0.0 can be found
`here <https://amt.copernicus.org/articles/17/4891/2024/>`_. In this page, we
list all changes since v.2.0.0 that go beyond bugfixing, refactoring, patching,
etc. and have an impact on the science of the algorithm. More detailed
information on changes can be found in the `changelog <changelog>`.


v2.1.0: Enable ceilometer filtering for calculation of cloud base height
------------------------------------------------------------------------

There might be situations, where it is beneficial to calculate the cloud base
height from a subset of ceilometer hits reported by specific ceilometers. For
example:
- If the cloud height is supposed to be representative for a given location, but
you still want to use as many ceilometers as possible to infer the amount.
- If you use different ceilometer models and know that you want to calculate the
height only from hits of a specific ceilometer model to avoid implementing
complicated correction factors.
To this end, the parameter ``CEILOS_FOR_BASE_HEIGHT_CALC`` was implemented in
this version. The default value is an empty list. In order to activate the
filtering, it is sufficient to enter the ceilometer IDs of the ceilos to keep
for the base height calculation.
