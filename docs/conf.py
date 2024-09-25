import time
import vercel_blob

project = 'vercel_blob'
author = 'Surya Sekhar Datta'
copyright = '%d, Surya Sekhar Datta' % time.gmtime().tm_year
version = vercel_blob.__version__
release = vercel_blob.__version__
master_doc = 'index'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'nbsphinx',
    'sphinxcontrib.bibtex',
]

bibtex_bibfiles = ['bibliography.bib']
bibtex_default_style = 'unsrt'

# templates_path = ['_templates']
# exclude_patterns = ['.build']

# rst_prolog = """
# """
language = "en"

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "tango"

# Execute content of Jupyter notebooks:
# "always", "never", "auto" (on empty cell only)
nbsphinx_execute = "never"

# Create stubs automatically for all auto-summaries:
autosummary_generate = True

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "external_links":
        [{"name": "Github", "url": "https://github.com/SuryaSekhar14/vercel_blob"}],
    # "footer_items": ["sphinx-version.html"],
    "navbar_align": "left",
    'repository_url': 'https://github.com/SuryaSekhar14/vercel_blob',
    # "navbar_end": ["search-field.html"],
    "navigation_depth": 4,
    # "show_prev_next": False,
}
html_short_title = "vercel_blob"
html_context = {
    "doc_path": "docs",
}
# html_logo = ""
# html_static_path = ['_static']
# html_sidebars = {
#     "**": ["sidebar-nav-bs.html"],
# }

htmlhelp_basename = 'vercel_blob'
html_show_sourcelink = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}