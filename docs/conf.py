# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


source_suffix = ['.rst', '.md']

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'w3rkstatt'
copyright = '2023, Volker Scheithauer'
author = 'Volker Scheithauer'
release = 'v:stable'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser"]
myst_enable_extensions = ["colon_fence","dollarmath"]




templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']


