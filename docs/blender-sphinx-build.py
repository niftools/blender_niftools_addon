# get site-packages into sys.path
import site
import sys

# run sphinx builder
import sphinx
sphinx.main(argv=sys.argv[3:])

# quit blender
import bpy
bpy.ops.wm.quit_blender()
