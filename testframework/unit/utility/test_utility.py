import nose
from nose import with_setup

import pyffi
from pyffi.formats.nif import NifFormat

import io_scene_nif
from io_scene_nif.utility import utilities

class Test_Utilites:
    
    @classmethod
    def setUpClass(cls):
        print("Setup" + str(cls))
        cls.niBlock = NifFormat.NiNode()
        
        
    @classmethod
    def tearDownClass(cls):
        print("Teardown" + str(cls))
        cls.niBlock = None
        
        
    def test_import_matrix(self):
        print("Running ")
        
        pass
        #import_matrix(self, niBlock, relative_to=None):