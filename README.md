# ampycloud

[![github](https://img.shields.io/github/release/MeteoSwiss/ampycloud.svg)](https://github.com/MeteoSwiss/ampycloud/releases)
[![last-commit](https://img.shields.io/github/last-commit/MeteoSwiss/ampycloud.svg?colorB=e6c000)](https://github.com/MeteoSwiss/ampycloud)
[![issues](https://img.shields.io/github/issues/MeteoSwiss/ampycloud.svg?colorB=b4001e)](https://github.com/MeteoSwiss/ampycloud/issues)
[![pypi](https://img.shields.io/pypi/v/ampycloud.svg?colorB=<brightgreen>)](https://pypi.python.org/pypi/ampycloud/)

### Introduction

ampycloud refers to both this Python package and the algorithm in its core. Both are designed to characterize cloud layers (i.e. height and sky coverage fraction) from ceilometer measurements, and specifically: automatic cloud base *hits* measurements.

If this code ever makes it out in the open, you'll be able to check the full documentation at
https://MeteoSwiss.github.io/ampycloud

### License & Copyright

ampycloud is released under the terms of **the 3-clause BSD license**. The copyright belongs to MeteoSwiss.

### Installation instructions

Until further notice, ampycloud needs to be installed locally. After downloading the code on your machine (or cloning the repo, if you prefer), `cd` into the repo at the level of `setup.py`, and
do a local pip install via:
```
pip install -e .
```

This will take care of things, including the installation of required dependencies.

**For devs:** if you plan to contribute to ampycloud, you will also need a few additional tools:
```
pip install -r ./.dev_utils/dev_requirements.txt
```

### Logging

A `NullHandler()` is being set by ampycloud, such that no logging will be apparent to the users
unless they explicitly set it up
(see [here](https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library) for details).

As an example, to enable ampycloud log messages down to the 'DEBUG' level, users could make the following call before running ampycloud functions:
```
import logging

logging.basicConfig()
logging.getLogger('ampycloud').setlevel('DEBUG')
```
Each ampycloud module has a dedicated `logger` based on its `__name__`, such that users can adjust
the parameter of each ampycloud module however they desire, e.g.:
```
logging.getLogger('ampycloud.wmo').setlevel('WARNING')
logging.getLogger('ampycloud.scaler').setlevel('DEBUG')
```


### Contributing to ampycloud

Please see the [contributing guidelines](CONTRIBUTING.md) for details.
