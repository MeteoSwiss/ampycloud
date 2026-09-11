# -*- coding: utf-8 -*-
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os

# -- Project information -----------------------------------------------------

project = "ampycloud"
copyright = "2021-2026, MeteoSwiss"
author = "ampycloud"

version = os.getenv("VERSION", default="")
build_id = os.getenv("BUILD_ID", default="")
release = f"{version}-{build_id}"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",  # To get the TODOs visible
    "sphinx.ext.autosectionlabel",  # So we can link directly to the section header names
    "sphinx.ext.autodoc",  # To get the automatic documentation of functions
    "sphinx.ext.viewcode",
    "autoapi.extension",  # Auto-generated API reference (replaces sphinx-apidoc)
]

# Specify the parameters of the autodoc
autodoc_default_options = {
    "member-order": "bysource",  # List fcts and classes in the same order they are in the files
}

# To use this nice feature, but still avoid wreaking havoc with autoapi
autosectionlabel_prefix_document = True

exclude_patterns = ["_build"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

highlight_language = "python3"

# Deal with the todos
todo_include_todos = True
todo_link_only = False

# Napoleon settings (for the docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = False  # improve parameters description
napoleon_use_rtype = False
napoleon_use_keyword = False
napoleon_custom_sections = None

add_module_names = False  # avoid the display of redundant module names

# Enable the numbering of Figures
numfig = True

# sphinx-autoapi settings: point at the ampycloud package under the src/ layout.
autoapi_dirs = ["../src/ampycloud"]
autoapi_options = ["members", "undoc-members", "show-inheritance", "show-module-summary", "imported-members"]

# -- Options for HTML output -------------------------------------------------

html_title = project
html_theme = "pydata_sphinx_theme"

html_last_updated_fmt = "%d.%m.%Y"

html_theme_options = {
    "show_nav_level": 2,
    "navigation_depth": 4,
    "show_toc_level": 1,
    "secondary_sidebar_items": ["page-toc"],
    "logo": {
        "text": project,
        "image_light": "_static/app-icon_meteoswiss_rounded_rgb.png",
        "image_dark": "_static/app-icon_meteoswiss_rounded_rgb.png",
    },
    "switcher": {
        "json_url": os.getenv("VERSION_SWITCHER_CONFIG_URL", "_static/switcher_config.json"),
        "version_match": os.getenv("VERSION", "dev"),
    },
    "navbar_end": ["navbar-icon-links", "theme-switcher", "version-switcher"],
    "footer_start": ["version", "last-updated", "copyright"],
    "footer_end": ["theme-version", "sphinx-version"],
}

# Disable left side navigation of specific pages, since they are empty
# (BUG in theme: https://github.com/pydata/pydata-sphinx-theme/issues/1662)
html_sidebars = {"changelog": [], "license": [], "scope": []}
