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

### Exceptions and Warnings

The class `AmpyCloudError` defined in `errors.py` is a child of the canonical Python `Exception`
class, and is meant as a general exception for ampycloud. Using it is straightforward:
```
from .errors import AmpycloudError

raise AmpycloudError('...')
```

There is also a custom `AmpycloudWarning` class for the package, which is a simple child of the
`Warning` class. Using it is simple:
```
import warnings
from .errors import AmpycloudWarning

warnings.warn('...', AmpycloudWarning)
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
  some_fct(*args, *kwargs):
      ...
  ```

### Testing

A series of test functions are implemented under `test`. Their structure mimics that of the module
itself, and they are meant to be used with pytest. To run them all, simply type `pytest` in a terminal from the package root. If you only want to run a specific set of tests, type `pytest test/ampycloud/module/to/test_...py`.

In order to test the different plotting style without affecting the automated tests on Github (which cannot do so because they have no access to a local LaTeX installation), a nifty fixture is
defined in `conftext.py`, that allows to feed a specific command line argument to the pytest call:
```
pytest --MPL_STYLE=latex
```
Doing so, the users can easily test the `dynamic.MPL_STYLE` of their choice, e.g. `base`, `latex`, or `metsymb`. :warning: For this to work, pytest must be called from the package root.


### Plotting

Because the devs care about the look of plots, ampycloud ships with specific matplotlib styles that will get used by default. For this to work as intended, any plotting function must be wrapped with the `plots.utils.set_mplstyle` decorator, as follows:
```
# Import from Python
import logging

# Import from this module
from ..logger import log_func_call
from .utils import set_mplstyle

# Instantiate the module logger
logger = logging.getLogger(__name__)

@set_mplstyle
@log_func_call(logger)
def some_plot_function(...):
    ...
```
Note how the `@set_mplstyle` decorator goes above the `@log_func_call()` decorator.

With this decorator, all functions will automatically deploy the effects associated to the value of `dynamic.AMPYCLOUD_PRMS.MPL_STYLE` which can be one of the following: `['base', 'latex', 'metsymb']`.
