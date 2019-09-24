"""Export and import ninode based armatures."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from integration import SingleNif
from integration.data import n_gen_header


class TestNiNodeArmature(SingleNif):
    """Test NiNode base armature"""

    g_path = 'armature/ninode'
    g_name = 'test_armature'
    b_name = 'Armature'

    def b_create_data(self):
        raise NotImplementedError
        
    def b_check_data(self):
        raise NotImplementedError
    
    def n_create_data(self):
        raise NotImplementedError

    def n_check_data(self):
        raise NotImplementedError
