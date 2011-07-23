# get site-packages into sys.path
import site
import sys

# run sphinx builder
# this assumes that the builder is called as
# "blender -P blender-sphinx-build.py -- ..."
# sys.argv[3:] passes the correct arguments onto the builder by
# dropping the first three arguments
import sphinx
sphinx.main(argv=sys.argv[3:])

# quit blender
import bpy
bpy.ops.wm.quit_blender()
