"""
Assumes file is called as follows
"blender --background --factory-startup --python blender-nosetests.py ... ... ... ..."

Useful additional params:
-s : stdout is not captured by default, eg print().
--with-xunit, --with-coverage 
"""

import sys
import nose

# Nose internally uses sys.argv for paramslist, prune extras params from chain, add name param
sys.argv = ['blender-nosetests'] + sys.argv[6:]
nose.run_exit()

