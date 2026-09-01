# Contributing guidelines

If you:

* :boom: want to **report a bug** with ampycloud: [jump here.](https://github.com/MeteoSwiss/ampycloud/issues)
* :question: have a **question** about ampycloud: [jump here instead.](https://github.com/MeteoSwiss/ampycloud/discussions)
* :construction_worker: want to **contribute** to ampycloud, read on !


## Table of contents

- [Code of conduct](#code-of-conduct)
- [Scope](#scope)
- [Essential things to know about ampycloud for dev work](#essential-things-to-know-about-ampycloud-for-dev-work)
    - [Branching model](#branching-model)
    - [Installing from source](#installing-from-source)
    - [CI/CD](#cicd)
    - [Linting](#linting)
    - [Logging](#logging)
    - [Exceptions and Warnings](#exceptions-and-warnings)
    - [Type hints](#type-hints-)
    - [Docstrings](#docstrings)
    - [Documentation](#documentation)
    - [Testing](#testing)
    - [Plotting](#plotting)
    - [Release mechanism](#release-mechanism)
- [Less-Essential things to know about ampycloud for dev work](#less-essential-things-to-know-about-ampycloud-for-dev-work)
    - [Updating the copyright years](#updating-the-copyright-years)


## Code of conduct

This project and everyone participating in it is governed by the [ampycloud Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.
Please report unacceptable behavior to [loris.foresti@meteoswiss.ch](mailto:loris.foresti@meteoswiss.ch).

## Scope

Please be sure to read (and understand the implications) of the
[scope of ampycloud](https://meteoswiss.github.io/ampycloud/index.html#scope-of-ampycloud).

## Essential things to know about ampycloud for dev work

ampycloud is being developed in a **public** repository under the [MeteoSwiss organization](https://github.com/MeteoSwiss/ampycloud) on Github. The documentation, generated using Sphinx, is hosted as Github Pages on the `gh-pages` branch of the repo, and is visible at https://MeteoSwiss.github.io/ampycloud.

### New developer

Please make sure to read the instructions below carefully. In addition, please add your name to the software part of the [citation](#CITATION.cff) file at the latest before triggering
a [release](#release-mechanisms)(the top part defines the citation for the software, the bottom part defines the citation of the scientific article) and make sure to properly
update the CHANGELOG and the [documentation](#documentation) if necessary.

### Branching model

The `main` branch is the default one, where all contributions get merged.

Contributors are required to work in their own branches, and issue Pull Requests into the `main`
branch when appropriate.

The `main`, and `gh-pages` branches are all protected.

The naming convention for branches is as follows:
- bugfix/<JIRA_TASK>_Description
- feature/<JIRA_TASK>_Description

The daily workflow is as follows:
```
git checkout main
git pull origin main
git checkout -b feature/JIRA_my-new-feature  # or bugfix/JIRA_my-new-feature
```


### Installing from source

If you intend to actively contribute to ampycloud, you ought to clone the `main` branch of the
repository, and install it from source. In a terminal:
```
git clone -b main git@github.com:MeteoSwiss/ampycloud.git some_folder
cd some_folder
poetry install
```


### CI/CD

Automated CI/CD checks are triggered upon Pull Requests being issued towards any branch, and upon
pushes to `main`. At the time being, they are implemented using dedicated Github Actions specified
under `.github/workflows`. These checks include:

* code formatting using `ruff`
* code linting using `pylint`
* static type checking using `mypy`
* code testing using `pytest` (with a minimum coverage threshold)
* check that the Sphinx docs compile
* check that the base computational speed is ok (for PRs towards `main`)

Sphinx docs are published automatically: the `dev` documentation is rebuilt and published every
time `CI_test` succeeds on `main`, while versioned documentation is published together with the
PyPI package whenever a new tag is pushed (see below).

To test the latest release of the code with the latest Python developments, a `pytest-weekly` workflow runs the
ampycloud tests twice a week using the latest version of Python and of the ampycloud dependencies.

:warning: This test is being run from the `main` branch. Pushing a bug fix to a feature/bugfix branch will not be sufficient to make it turn green - it must first be merged into `main` !

There is another Github action responsible for publishing the code (and its documentation) onto pypi,
that gets triggered upon a new git tag being pushed, using PyPI's trusted publisher mechanism (no
API token required). See the ampycloud [release mechanisms](#release-mechanisms) for details.

### Linting with Pylint

Run pylint to check for code quality issues:

```console
$ poetry run pylint ampycloud
```

### Formatting with Ruff

We use [Ruff](https://docs.astral.sh/ruff/formatter) for code formatting with a 120-character line limit.

Format your code before committing:

```console
$ poetry run ruff format
```

### Logging

  No handlers/formatters are being defined in ampycloud, with the exception of a `NullHandler()` for
  when users do not specify any logging handler explicitly. In other words, [**it is up to the
  ampycloud users to decide what logging they wish to see**](https://MeteoSwiss.github.io/ampycloud/running.html#logging), if any.

  Specifically:

  * a dedicated logger gets instantiated in each ampycloud module via:

    ```
    import logging
    logger = logging.getLogger(__name__)
    ```
  * log calls are then simply done via this module logger:

    ```
    logger.debug('...')
    logger.info('...')
    logger.warning('...')
    logger.error('...')
    ```

  * the function `ampycloud.logger.log_func_call()` can be used to decorate ampycloud functions and
    automatically log their call at the `INFO` level, and the arguments at the `DEBUG` level, e.g.:

    ```
    import logging
    from .logger import log_func_call

    logger=logging.getLogger(__name__)

    @log_func_call(logger)
    some_fct(*args, *kwargs):
        ...
    ```

### Exceptions and Warnings

The class `AmpycloudError` defined in `errors.py` is a child of the canonical Python `Exception`
class, and is meant as a general exception for ampycloud. Using it is straightforward:
```
from .errors import AmpycloudError

raise AmpycloudError('...')
```

There is also a custom `AmpycloudWarning` class for the package, which is a simple child of the
`Warning` class. Using it is also simple:
```
import warnings
from .errors import AmpycloudWarning

warnings.warn('...', AmpycloudWarning)
```

### Type hints ...

... should be used in ampycloud. Here's an example:
```
from typing import Union
from pathlib import Path


def set_prms(pth : Union[str, Path]) -> None:
    """ ... """
```
See [the official Python documentation](https://docs.python.org/3/library/typing.html) for more info.

### Docstrings
Google Style ! Please try to stick to the following example. Note the use of `:py:class:...`
([or `:py:func:...`, `py:mod:...` etc ...](https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#cross-referencing-python-objects)) with relative import to cleanly link to our own
functions, classes, etc ... :
```
""" A brief one-liner description in present tense, that finishes with a dot.

Args:
    x (float|int): variable x could be of 2 types ... note the use of `|` to say that !
        - *float*: x could be a float
        - *int*: x could also be an int

    y (list[str]|str, optional): variable y info

Returns:
    :py:class:`.data.CeiloChunk`: more lorem ipsum ...

Raises:
    :py:exc:`.errors.AmpycloudError`: if blah and blah occurs.


Use some
multi-line space for
more detailed info. Refer to the whole module as :py:mod:`ampycloud`.
Do all this **after** the Args, Returns, and Raises sections !

Example:
    If needed, you can specify chunks of code using code blocks::

        def some_function():
            print('hurray!')

Note:
    `Source <https://github.com/sphinx-doc/sphinx/issues/3921>`__
    Please note the double _ _ after the link !

Important:
   Something you're hoping users will read ...

Caution:
    Something you're hoping users will read carefully ...

"""
```

You should of course feel free to use more of the tools offered by
[sphinx](https://www.sphinx-doc.org/en/master/),
[napoleon](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html), and
[Google Doc Strings](https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html#example-google). But if you do, **please make sure there are no errors upon generating the docs !**


### Documentation

There is a [scientific article](https://amt.copernicus.org/articles/17/4891/2024/) about the ampycloud **algorithm** v2.0.0. It complements
the [Sphinx documentation](https://MeteoSwiss.github.io/ampycloud) that contains all the important elements required to use the ampycloud **Python package**. Scientific changes
on top of version v2.0.0 must be added to [the corresponding section in the docs](https://meteoswiss.github.io/ampycloud/changes.html).

The Sphinx documentation can be generated manually as follows:
```
cd ./where/you/placed/ampycloud/docs
sh build_docs.sh
```
This will create the `.html` pages of the compiled documentation under `./build`. In particular,
this bash script will automatically update the help message from the high-level ampycloud entry
point ``ampycloud_speed_test``, create the demo figure for the main page, compile and ingest all the
docstrings, etc ... . See the ampycloud [release mechanisms](#release-mechansims) for more info about
the automated publication of the documentation upon new releases.


### Testing

A series of test functions are implemented under `test`. Their structure mimics that of the module
itself, and they are meant to be used with pytest. To run them all, simply type `pytest` in a
terminal from the package root. If you only want to run a specific set of tests, type
`pytest test/ampycloud/module/to/test_...py`.

In order to test the different plotting styles without affecting the automated tests on Github
(which cannot do so because they have no access to a local LaTeX installation), a nifty fixture is
defined in `conftext.py`, that allows to feed a specific command line argument to the pytest call:
```
pytest --MPL_STYLE=latex
```
Doing so, the users can easily test the `dynamic.MPL_STYLE` of their choice, e.g. `base`, `latex`,
or `metsymb`. :warning: For this to work, pytest must be called from the package root.

The tests defined under `test/ampycloud/test_scientific_stability.py` are meant to catch any unexpected alteration of the **scientific behavior** of ampycloud. Specifically, they process real
datasets of reference, and check whether the computed METARs are as expected. The reference
datasets are provided as CSV files under `test/ampycloud/ref_dat`. The idea is to keep
this list of scientific tests *as short as possible, but as complete as necessary*.

If one of these tests fail, it is possible to generate the corresponding diagnostic plot with the
following fixture-argument:
```
pytest --DO_SCIPLOTS
```

### Plotting

Because the devs care about the look of plots, ampycloud ships with specific matplotlib styles that
will get used by default. For this to work as intended, any plotting function must be wrapped with
the `plots.utils.set_mplstyle` decorator, as follows:
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
:warning: Note how the `@set_mplstyle` decorator goes above the `@log_func_call()` decorator.

With this decorator, all functions will automatically deploy the effects associated to the value of `dynamic.AMPYCLOUD_PRMS['MPL_STYLE']` which can take one of the following values:
`['base', 'latex', 'metsymb']`.

### Release mechanism

When changes merged into `main` are stable and deemed *worthy*, follow these steps to create a
new release of ampycloud:

1) Open a PR into `main` that bumps `src/ampycloud/version.py` to the new version number, and
   merge it once all `CI_test` checks pass.

   :white_check_mark: Merging to `main` triggers `CI_publish_dev_documentation.yaml`, which
   rebuilds and publishes the `dev` version of the
   [live ampycloud documentation](https://MeteoSwiss.github.io/ampycloud).

2) Push a git tag (e.g. `vX.Y.Z`) from `main`, at the commit that bumped the version.

   :warning: **The tag (minus its leading `v`) must exactly match `VERSION` in
   `src/ampycloud/version.py`** — `CI_publish.yaml` checks this explicitly and will fail the
   workflow if they differ.

   :white_check_mark: Pushing the tag triggers `CI_publish.yaml`, which re-runs the full test
   suite, then builds and publishes the package to pypi using
   [PyPI's trusted publisher mechanism](https://docs.pypi.org/trusted-publishers/) (an OIDC-based
   exchange — no long-lived API token involved), and builds and publishes the versioned
   documentation for that release to the `gh-pages` branch. This works the same for pre-release
   tags.

3) That's it ! Wait a few seconds/minutes, and you'll see the updates:

   - on the [release page](https://github.com/MeteoSwiss/ampycloud/releases) (create one manually
     from the pushed tag if you want release notes),
   - in the [README](https://github.com/MeteoSwiss/ampycloud/blob/main/README.md) tags,
   - on [pypi](https://pypi.org/project/ampycloud/),
   - on the [`gh-pages` branch](https://github.com/MeteoSwiss/ampycloud/tree/gh-pages),
   - in the [live documentation](https://MeteoSwiss.github.io/ampycloud), and
   - on [Zenodo](https://zenodo.org/doi/10.5281/zenodo.8399683) (for which the connection to this repo is enabled from Zenodo itself, by the admins of the MeteoSwiss organization on Github).

## Less-Essential things to know about ampycloud for dev work

### Updating the copyright years
The ampycloud copyright years may need to be updated if the development goes on beyond 2022 (which it already has 😉). If so,
the copyright years will need to be manually updated in the following locations:

* `docs/source/substitutions.rst` (the copyright tag)
* `docs/source/conf.py` (the `copyright` variable)
* `docs/source/license.rst`
* `README.md` (the copyright section)

The copyright years are also present in all the docstring modules. These can be updated individually
if/when a modification is made to a given module.
