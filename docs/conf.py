"""Sphinx configuration for the aiographql-client documentation."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath("../src"))


# -- Project information -----------------------------------------------------

project = "Async GraphQL Client"
_authors = "Arun Neelicattu, Maria Soulountsi, Josha Inglis"
copyright = f"2019-{datetime.now(tz=timezone.utc).year}, {_authors}"
author = _authors


# -- General configuration ---------------------------------------------------

master_doc = "index"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinxext.opengraph",
    "sphinx_sitemap",
    "notfound.extension",
    "sphinxcontrib.mermaid",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "_includes"]

html_last_updated_fmt = "%b %d, %Y"


# -- HTML output -------------------------------------------------------------

html_theme = "shibuya"
html_favicon = "images/favicon.ico"
# `images/` is mirrored into `_static/` so the hero can reference logos
# via `_static/...` paths.
html_static_path = ["_static", "images"]
html_css_files = ["custom.css"]
html_show_sourcelink = False
html_baseurl = "https://aiographql-client.readthedocs.io/en/latest/"

html_theme_options = {
    "accent_color": "pink",
    "globaltoc_expand_depth": 1,
    "light_logo": "_static/aiographql-client-logo.svg",
    "dark_logo": "_static/aiographql-client-logo-white.svg",
    "nav_links": [
        {"title": "Introduction", "url": "introduction"},
        {"title": "Examples", "url": "examples"},
        {"title": "API", "url": "api"},
        {"title": "Contributing", "url": "contributing"},
        {"title": "Changelog", "url": "changelog"},
    ],
    "github_url": "https://github.com/abn/aiographql-client",
}

# Drives the per-page "Edit this page" link.
html_context = {
    "source_type": "github",
    "source_user": "abn",
    "source_repo": "aiographql-client",
    "source_version": "main",
    "source_docs_path": "/docs/",
}


# -- autodoc / type hints ----------------------------------------------------

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
always_document_param_types = True
typehints_fully_qualified = False
typehints_use_signature = True
typehints_use_signature_return = True
# Annotations under `from __future__ import annotations` plus TYPE_CHECKING
# imports are unresolvable at autodoc introspection; signatures still render.
suppress_warnings = ["sphinx_autodoc_typehints.forward_reference"]


# -- intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
    "graphql-core": ("https://graphql-core-3.readthedocs.io/en/latest/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}


# -- copy button -------------------------------------------------------------

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = False
copybutton_remove_prompts = True


# -- Open Graph / social previews --------------------------------------------

ogp_site_url = "https://aiographql-client.readthedocs.io/"
ogp_site_name = "Async GraphQL Client"
ogp_image = (
    "https://aiographql-client.readthedocs.io/en/latest/"
    "_static/aiographql-client-logo.svg"
)
ogp_description_length = 200
ogp_type = "website"


# -- Sitemap -----------------------------------------------------------------

sitemap_url_scheme = "{link}"


# -- 404 page ----------------------------------------------------------------

# Read the Docs serves content under /<lang>/<version>/.
if os.environ.get("READTHEDOCS") == "True":
    notfound_urls_prefix = (
        f"/{os.environ.get('READTHEDOCS_LANGUAGE', 'en')}/"
        f"{os.environ.get('READTHEDOCS_VERSION', 'latest')}/"
    )
else:
    notfound_urls_prefix = "/"


# -- Mermaid -----------------------------------------------------------------

mermaid_version = "10.9.1"
mermaid_init_js = "mermaid.initialize({startOnLoad:true, theme:'default'});"


# -- MyST --------------------------------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "substitution",
]
