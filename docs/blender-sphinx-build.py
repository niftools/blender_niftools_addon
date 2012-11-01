import os
import site # for fedora: get site-packages into sys.path so it finds sphinx
import sys

# run sphinx builder
# this assumes that the builder is called as
# "blender --background --factory-startup --python blender-sphinx-build.py -- ..."
# pass the correct arguments by dropping the arguments prior to --
import sphinx
argv = ['blender-sphinx-build'] + sys.argv[6:]
sphinx.main(argv=argv)
