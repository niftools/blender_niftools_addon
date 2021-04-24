# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
import codecs

# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = "Blender NifTools Addon"
copyright = "2005, NifTools"
author = "NifTools"

# The full version, including alpha/beta/rc tags
with codecs.open("../io_scene_niftools/VERSION.txt", "rb", encoding="ascii") as f:
    release = f.read().strip()


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
]

# Include all todos
todo_include_todos = True

# Mock Import Blender
autodoc_mock_imports = ["bpy"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "blender": ("https://www.blender.org/api/blender_python_api_2_82_release/", None),
    "pyffi": ("https://pyffi.readthedocs.io", None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "niftools_sphinx_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "navs": {
        "Home": "http://niftools.org",
        "Out Projects": "http://www.niftools.org/projects",
        "Blog": "http://niftools.org/blog",
        "Documentation": "https://blender-niftools-addon.readthedocs.io",
        "Forums": "https://forum.niftools.org",
        "About": "http://niftools.org/about",
    },
    "source_code": "https://github.com/niftools/blender_niftools_addon",
}

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "_static/logo.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/favicon.ico"

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = "%b %d, %Y"
