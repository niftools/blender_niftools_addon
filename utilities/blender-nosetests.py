import os
import site # get site-packages into sys.path
import sys

# add local addons folder to sys.path so blender finds it
root = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
sys.path = (
    [os.path.join(root, 'scripts', 'addons')]
    + sys.path
    )

# run nosetests
# this assumes that the builder is called as
# "blender --background --factory-startup --python blender-nosetests.py -- ..."
# pass the correct arguments by dropping the arguments prior to --
import nose
sys.argv = ['blender-nosetests'] + ['-w', '..' + os.sep + 'test'] + sys.argv[6:]
nose.run_exit()