"""Exports and imports """

import bpy
import nose.tools
import io_scene_nif.export_nif
from pyffi.formats.nif import NifFormat
from test.test_cube import TestCube

class TestVertexColor(test.SimpleNif):
    n_name = "base_vertex_color"
    
    def b_create_object(self):
        b_obj = TestCube.b_create_object(self)
        return b_obj
    