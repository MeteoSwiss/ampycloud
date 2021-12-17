.. include:: ./substitutions.rst

.. _parameters:

The ampycloud scientific parameters
===================================

The default values of all the ampycloud parameters with a **scientific** impact on the outcome of
the algorithm are defined in ``src/ampycloud/prms/ampycloud_default_prms.yml``. For completeness
and ease of access, the content of this file is reproduced below.

.. note::

    With ampycloud installed on your machine, you can easily get a local copy of this file using
    the following high-level entry point accessible from the command line: ``ampycloud_copy_prm_file``.
    For more details, see
    :ref:`Adjusting the default algorithm parameters. <running:Adjusting the default algorithm parameters>`

.. warning::

    It is **very strongly** discouraged to modify this reference file directly. ampycloud offers
    other ways to modify the default parameter values to fit your needs, including via local
    copies of this file. See :ref:`Adjusting the default algorithm parameters <running:Adjusting the default algorithm parameters>`
    for details.

.. literalinclude:: ../../src/ampycloud/prms/ampycloud_default_prms.yml
    :language: yaml
