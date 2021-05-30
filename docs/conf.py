# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../src"))


# -- Project information -----------------------------------------------------

project = "Async GraphQL Client"
copyright = "2019, Arun Neelicattu, Maria Soulountsi, Josha Inglis"
author = "Arun Neelicattu, Maria Soulountsi, Josha Inglis"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
# version = u'3.0'
# The full version, including alpha/beta/rc tags.
# version = release = u'0.3.0a0'

# -- General configuration ---------------------------------------------------

master_doc = "index"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "readthedocs_ext.readthedocs",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "_includes"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_material"

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "images/aiographql-client-logo-white.svg"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "images/favicon.ico"

html_show_sourcelink = False
html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}

# Material theme options (see theme.conf for more information)
html_theme_options = {
    # Set the name of the project to appear in the navigation.
    "nav_title": "Async GraphQL Client",
    "nav_links": [
        {"href": "introduction", "internal": True, "title": "Introduction"},
        {"href": "examples", "internal": True, "title": "Usage Examples"},
        {"href": "api", "internal": True, "title": "Python API"},
        {"href": "contributing", "internal": True, "title": "Contributing"},
    ],
    "heroes": {
        "index": "An asynchronous GraphQL client for Python and asyncio.",
    },
    # Specify a base_url used to generate sitemap.xml. If not
    # specified, then no sitemap will be built.
    # "base_url": "https://aiographql-client.readthedocs.io/",
    # Set the color and the accent color
    "color_primary": "pink",
    "color_accent": "black",
    # Set the repo location to get a badge with stats
    "repo_url": "https://github.com/abn/aiographql-client",
    "repo_name": "Async GraphQL Client",
    # Visible levels of the global TOC; -1 means unlimited
    "globaltoc_depth": 2,
    # If False, expand all TOC entries
    "globaltoc_collapse": True,
    # If True, show hidden TOC entries
    "globaltoc_includehidden": True,
    "master_doc": False,
    # optimisation
    "html_minify": True,
    "css_minify": True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
