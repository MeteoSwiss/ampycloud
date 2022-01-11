# Contributing guidelines

If you:

*  :boom: want to **report a bug** with ampycloud: [jump here.](https://github.com/MeteoSwiss/ampycloud/issues)
*  :question: have a **question** about ampycloud: [jump here instead.](https://github.com/MeteoSwiss/ampycloud/discussions)
* :construction_worker: want to **contribute** to ampycloud (:heart_eyes: :tada:): read on !


## Table of contents

- [Code of conduct](#code-of-conduct)
- [Scope of ampycloud](#scope-of-ampycloud)
- [Essential things to know about ampycloud for dev work](#essential-things-to-know-about-ampycloud-for-dev-work)
    - [Branching model](#branching-model)
    - [Installing from source](#installing-from-source)
    - [CI/CD](#cicd)
    - [Linting](#linting)
    - [Logging](#logging)
    - [Exceptions and Warnings](#exceptions-and-warnings)
    - [Docstrings](#docstrings)
    - [Documentation](#documentation)
    - [Testing](#testing)
    - [Plotting](#plotting)
- [Less-Essential things to know about ampycloud for dev work](#less-essential-things-to-know-about-ampycloud-for-dev-work)
    - [Updating the copyright years](#updating-the-copyright-years)


## Code of conduct

This project and everyone participating in it is governed by the [ampycloud Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.
Please report unacceptable behavior to [loris.foresti@meteoswiss.ch](mailto:loris.foresti@meteoswiss.ch) and/or [frederic.vogt@meteoswiss.ch](mailto:frederic.vogt@meteoswiss.ch).


## Scope of ampycloud

Please be sure to read (and understand the implications) of the
[scope of ampycloud](https://meteoswiss.github.io/ampycloud/index.html#scope-of-ampycloud).

## Essential things to know about ampycloud for dev work

For now, ampycloud is being developed in a **private** repository under the [MeteoSwiss organization](https://github.com/MeteoSwiss/ampycloud) on Github. The documentation, generated using Sphinx, is hosted as Github Pages on the `gh-pages` branch of the repo, and is **publicly** visible
at https://MeteoSwiss.github.io/ampycloud.


### Branching model

The `develop` branch is the default one, where all contributions get merged. When a new release is
warranted, a Pull Request to the `master` branch is issued. This implies that the `master` branch
will always reflect the state of the latest release of the code.

Contributors are required to work in their own branches, and issue Pull Requests into the `develop`
branch when appropriate.

The `master`, `develop`, and `gh-pages` branches are all protected.


### Installing from source

If you intend to actively contribute to ampycloud, you ought to clone the `develop` branch of the
repository, and install it from source. In a terminal:
```
git clone -b develop git@github.com:MeteoSwiss/ampycloud.git some_folder
cd some_folder
pip install -e .[dev]
```
Note the use of `[dev]` to also install the dependencies required for dev work (i.e. `sphinx`, `pylint`, etc ...).

:warning: If you encouter the error `zsh: no matches found: .[dev]`, add some quotes as follows:
```
pip install -e '.[dev]'
```


### CI/CD

Automated CI/CD checks are triggered upon Pull Requests being issued towards the `develop` and
`master` branches. At the time being, they are implemented using dedicated Github Actions specified under `.github/workflows`. These checks include:

* code linting using `pylint`
* code testing using `pytest`
* check that the CHANGELOG was updated
* check that the Sphinx docs compile
* automatic publication of the Sphinx docs

Additional CI/CD tasks will be added eventually, including:

* automatic release mechanism, incl. pypi upload


### Linting:

* The following [pylint](https://www.pylint.org/) error codes are forbidden in ampycloud:
  ``E, C0303, C0304, C0112, C0114, C0115, C0116, C0411, W0611, W0612.`` Every Pull Request to `develop` and `master` is automatically linted, and these codes will be flagged accordingly.
* There is no "automated black formatting" implemented in the repo **by choice**. We believe that it
  is up to the contributors to ensure that the quality of their code meets the required standards enforced by the Github Action in this repo.
* We encourage contributors to follow PEP8 as closely as possible/reasonable. You should check
  often how well you are doing using the command `pylint some_modified_file.py`.



### Logging

  No handlers/formatters are being defined in ampycloud, with the exception of a `NullHandler()` for
  when users do not specify any logging handler explicitly. In other words, [**it is up to the
  ampycloud users to decide what logging they wish to see**](https://MeteoSwiss.github.io/ampycloud/running.html#logging), if any.

  Specifically:

  * a dedicated logger gets instantiated in each ampycloud module via:

    ```
    import logging
    logger = loggging.getLogger(__name__)
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

### Docstrings
Google Style ! Please try to stick to the following example:
```
""" A brief one-liner description in present tense, that finishes with a dot.

Use some
multi-line space for
more detailed info.

Args:
    x (float|int): variable x could be of 2 types ... note the use of `|` to say that !
        - *float*: x could be a float
        - *int*: x could also be an int

    y (list[str]|str, optional): variable y info

Returns:
    bool: some grand Truth about the World.

Raises:
    AmpycloudError: if blah and blah occurs.

Example:
    If needed, you can specify chunks of code using code blocks::

        def some_function():
            print('hurray!')

Note:
    `Source <https://github.com/sphinx-doc/sphinx/issues/3921>`__
    Please note the double _ _ after the link !

Caution:
    Something to be careful about.

"""
```

You should of course feel free to use more of the tools offered by
[sphinx](https://www.sphinx-doc.org/en/master/),
[napoleon](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html), and
[Google Doc Strings](https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html#example-google). But if you do, **please make sure there are no errors upon generating the docs !**


### Documentation

There is a scientific article about the ampycloud **algorithm** in preparation. It will complement
the [Sphinx documentation](https://MeteoSwiss.github.io/ampycloud) that contains all the important elements required to use the ampycloud **Python package**.

The Sphinx documentation can be generated manually as follows:
```
cd ./where/you/placed/ampycloud/docs
sh build_docs.sh
```
This will create the `.html` pages of the compiled documentation under `./build`. In particular,
this bash script will automatically update the help message from the high-level ampycloud entry
point ``ampycloud_speed_test``, create the demo figure for the main page, compile and ingest all the
docstrings, etc ...


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
datasets are provided as Python pickle files under `test/ampycloud/ref_dat`. The idea is to keep
this list of scientific tests *as short as possible, but as complete as necessary*.

If one of these tests fail, it is possible to generate the corresponding diagnostic plot with the
following fixture-argument:
```
pytest --DO_SCIPLOTS
```

### Plotting

Because the devs care about the look of plots, ampycloud ships with specific matplotlib styles that will get used by default. For this to work as intended, any plotting function must be wrapped with
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

With this decorator, all functions will automatically deploy the effects associated to the value of `dynamic.AMPYCLOUD_PRMS.MPL_STYLE` which can take one of the following values:
`['base', 'latex', 'metsymb']`.

## Less-Essential things to know about ampycloud for dev work

### Updating the copyright years
The ampycloud copyright years may need to be updated if the development goes on beyond 2022. If so,
the copyright years will need to be manually updated in the following locations:

* `docs/source/substitutions.rst` (the copyright tag)
* `docs/source/conf.py` (the `copyright` variable)
* `docs/source/license.rst`
* `README.md` (the copyright section)

The copyright years are also present in all the docstring modules. These can be updated individually
if/when a modification is made to a given module.
