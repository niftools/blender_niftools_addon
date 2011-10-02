# get site-packages into sys.path
import site
import sys

# run nosetests
# this assumes that the builder is called as
# "blender --background --factory-startup --python blender-nosetests.py -- ..."
# pass the correct arguments onto the builder by
# dropping the arguments prior to --
import nose
sys.argv = ['blender-nosetests'] + sys.argv[6:]
nose.run_exit()
