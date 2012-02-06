"""Exports and imports vertex color"""

import bpy
import nose.tools
import test
import os
from pyffi.formats.nif import NifFormat

class TestVertexColor(test.SingleNif):
    n_name = "base_vertex_color"
    b_name = "Cube"
        
    def b_create_object(self):
        #TODO Remove and use TestCube as base.
        # note: primitive_cube_add creates object named "Cube"
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects["Cube"]
        # primitive_cube_add creates a double sided mesh; fix this
        b_obj.data.show_double_sided = False
        
        '''
        keys = (0,1,2)
        values = [(0,1,2),
                  (4,7,6),
                  (0,4,5)]
        facevalues = dict(keys,values)
        '''
        
        #vertex color specific stuff
        bpy.ops.paint.vertex_paint_toggle() #auto-gens a MeshColorLayer
        bpy.data.meshes['Cube'].vertex_colors["Col"].name = "VertexColor"
        
        '''
        for face, verts in facevalues:
            for vert_index, vert_val in enumerate(verts):
                if vert_index == 0:
                    bpy.data.objects['Cube'].data.vertex_colors[face].data[vert].color1.r = 0.0
                    bpy.data.objects['Cube'].data.vertex_colors[face].data[vert].color1.g = 1.0
                    bpy.data.objects['Cube'].data.vertex_colors[face].data[vert].color1.b = 1.0
                elif(vert_index == 1):
                    bpy.data.objects['Cube'].data.vertex_colors[face].data[vert].color2.r = 0.0
                    bpy.data.objects['Cube'].data.vertex_colors[face].data[vert].color2.g = 1.0
                    bpy.data.objects['Cube'].data.vertex_colors[face].data[vert].color2.b = 1.0
                else:
                    bpy.data.objects['Cube'].data.vertex_colors[face].data[vert].color3.r = 0.0
                    bpy.data.objects['Cube'].data.vertex_colors[face].data[vert].color3.g = 1.0
                    bpy.data.objects['Cube'].data.vertex_colors[face].data[vert].color3.b = 1.0
        '''
        return b_obj
    
    def b_check_object(self, b_obj):
        print("COMPARING BLENDER OBJ")
        
    def n_check_data(self, n_data):
        print("COMPARING NIF DATA")
        
    
    