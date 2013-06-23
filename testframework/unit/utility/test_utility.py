import nose
from nose import with_setup

import pyffi
from pyffi.formats.nif import NifFormat

import io_scene_nif
from io_scene_nif.utility import utilities

niBlock = NifFormat.NiNode()
obj = ""

def setup_func():
    print("\nSetup")
    global obj 
    obj = "object setup complete"
    
def teardown_func():
    print("Tear Down")

@with_setup(setup_func, teardown_func)
def test_import_matrix():
    print("Running ")
    print(obj)
    pass
    #def import_matrix(self, niBlock, relative_to=None):