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
* check that the SPinx docs compile

Additional CI/CD tasks will be added if this code ever makes it out into the open, including:

* automatic publication of the Shinx docs
* automatic release mechanism, incl. pypi upload
