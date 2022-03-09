ampycloud is a key dependency of the automatic METAR-generating code of MeteoSwiss,
which requires all its dependencies to be robust and stable.

This has the following implications for ampycloud:

    * The scope of ampycloud will remain limited to the **automatic processing of ceilometer
      hits**.  In particular, ampycloud does not process Vertical Visibility (VV) measurements.
      Depending on the ceilometer type, the user will need to decide how to treat VV hits *before*
      passing them to ampycloud, e.g. by removing them or by converting them to cloud base
      heights.

    * ampycloud can evidently be used for R&D work, but the code itself should not be
      seen as an R&D platform.

    * Contributions via Pull Requests are always welcome (and appreciated !), but will only be
      considered if they:

        - remove a bug, and/or
        - improve the usability of ampycloud without altering the quality of the results, and/or
        - demonstrate a significant improvement in the quality of the results.

    * The ingestion of external contributions may be delayed to allow for a careful, internal
      verification that they do not affect the MeteoSwiss operational chain that relies on
      ampycloud.

    * ampycloud is designed (and intended to be used) as a regular Python module. As such, it is
      not meant to interact (directly) with other programming languages. The implementation of a
      complex API to interact with "the outside World" (e.g. to feed data to ampycloud using the
      JSON format) is not foreseen.

    * ampycloud is not meant to handle/generate/derive ``CB/TCU`` codes. The module deals with
      "basic" cloud layers only.
