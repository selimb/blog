import os

import sphinx.application
import sphinx.config
import sphinx.builders.html
import sphinx.jinja2glue

# -- Project information -----------------------------------------------------

project = 'TESTPROJECTNAME'
copyright = '2021, Selim Belhaouane'
author = 'Selim Belhaouane'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "papyrus.contrib.jinja_hazmat",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Jinja Hazmat ------------------------------------------------------------

jinja_hazmat_enabled = True  # XXX use environment variable

def cb_builder_inited(app: sphinx.application.Sphinx) -> None:
    builder: sphinx.builders.html.StandaloneHTMLBuilder = app.builder


def setup(app: sphinx.application.Sphinx):
    app.connect("builder-inited", cb_builder_inited)