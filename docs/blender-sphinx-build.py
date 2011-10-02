# get site-packages into sys.path
import site
import sys

# run sphinx builder
# this assumes that the builder is called as
# "blender --background --factory-startup --python blender-sphinx-build.py -- ..."
# sys.argv[5:] passes the correct arguments onto the builder by
# dropping the first four arguments
import sphinx
sphinx.main(argv=sys.argv[5:])
