import os
import site # for fedora: get site-packages into sys.path so it finds nose
import sys

# run nosetests
# this assumes that the builder is called as
# "blender --background --factory-startup --python blender-nosetests.py -- ..."
# pass the correct arguments by dropping the arguments prior to --
import nose2
sys.argv = ['blender-nose2tests'] + sys.argv[6:]
nose2.main()