# Contributing guidelines

For now, ampycloud is being developed in a **private** repository under the
[MeteoSwiss organization](https://github.com/MeteoSwiss/ampycloud) on Github.

### Branching model

The `develop` branch is the default one, where all contributions get merged. When a new release is
warranted, a Pull Request to the `master` branch is issued. This implies that the `master` branch
will always reflect the state of the latest release of the code.

Contributors are required to work in their own branches, and issue Pull Requests into the `develop`
branch when appropriate.

If ampycloud ever makes it out in the open, the Sphinx doc will be published under the `gh-pages`
branch, and available under http://meteoswiss.github.io/ampycloud

The `master`, `develop`, and `gh-pages` branches are all protected.

### CI/CD
Automated CI/CD checks are triggered upon Pull Request being issued towards the `develop` and `master`
branches. At the time being, these include:

* code linting using `pylint`
* code testing using `pytest`
* check that the CHANGELOG was updated
* check that the Sphinx docs compile

Additional CI/CD tasks will be added if this code ever makes it out into the open, including:

* automatic publication of the Sphinx docs
* automatic release mechanism, incl. pypi upload


### Package documentation

We have a scientific article about the ampycloud **algorithm** in preparation. If you would like
access to it before it is published, contact @fpavogt.

The Python package documentation is generated using Sphinx, and is anticipated to be hosted using
Github Pages (with the live site present under the `gh-pages` branch of this repo) -- assuming
the code ever sees the light of day.

Until then, the doc can be generated manually as follows:
```
cd ./where/you/placed/ampycloud/docs
sh build_docs.sh
```
This will create the docs locally under `./build`.

### Exceptions

The class `AmpyCloudError` defined in `errors.py` is a child of the canonical Python `Exception`
class, and is meant as a general exception for ampycloud. Using it is straightforward:
```
from .errors import AmpycloudError

raise AmpycloudError('...')
```

### Logging

No handlers/formatters are being defined in ampycloud, with the exception of a `NullHandler()` for
when users do not specify any logging handler explicitly. In other words, **it is up to the ampycloud users to decide what logging they wish to see**, if any.

Specifically:

* a dedicated logger gets instantiated in each ampycloud module via:

  ```
  import logging
  logger = loggging.getLogger(__name__)
  ```
* log calls are simply done via their module logger:

  ```
  logger.debug('...')
  logger.info('...')
  logger.warning('...')
  logger.error('...')
  ```

* the function `ampycloud.logger.log_func_call()` can be used to decorate ampycloud functions to log
  their call at the `INFO` level, and the arguments at the `DEBUG` level, e.g.:

  ```
  import logging
  from .logger import log_func_call

  logger=logging.getLogger(__name__)

  @log_func_call(logger)
  @some_fct(*args, *kwargs):
      ...
  ```
