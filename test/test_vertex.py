"""Exports and imports vertex color"""

import bpy
import nose.tools
import test
import os
from pyffi.formats.nif import NifFormat

class TestVertexColor(test.SingleNif):
    n_name = "base_uv_texture"
    b_name = "Cube"
        
    def b_create_object(self):
        # note: primitive_cube_add creates object named "Cube"
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects["Cube"]
        # primitive_cube_add creates a double sided mesh; fix this
        b_obj.data.show_double_sided = False
        
        #vertex color specific stuff
        bpy.ops.paint.vertex_paint_toggle() #auto-gens a MeshColorLayer
        
        return b_obj
    
    def b_check_object(self, b_obj):
        print("COMPARING BLENDER OBJ")
        
    def n_check_data(self, n_data):
        print("COMPARING NIF DATA")
        
    
    