"""
Assumes file is called as follows
"blender --background --factory-startup --python blender-nosetests.py ... ... ... ..."

Useful additional params:
-s : stdout is not captured by default, eg print().
--with-xunit, --with-coverage 
"""

import os
import site # for fedora: get site-packages into sys.path so it finds nose
import sys

# Nose internally uses sys.argv for paramslist, prune extras params from chain, add name param 
sys.argv = ['blender-nosetests'] + sys.argv[6:]


import nose
nose.run_exit()

