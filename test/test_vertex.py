"""Exports and imports vertex color"""

import bpy
import nose.tools
import os

import io_scene_nif.export_nif
from pyffi.formats.nif import NifFormat
from test.test_cube import TestCube

class TestVertexColor(TestCube):
    n_name = "base_vertex_color"
    b_name = "Cube"
        
    def b_create_object(self):
        '''
        # note: primitive_cube_add creates object named "Cube"
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects["Cube"]
        # primitive_cube_add creates a double sided mesh; fix this
        b_obj.data.show_double_sided = False
        '''
        #TODO Remove and use TestCube as base.
        b_obj = TestCube.b_create_object(self)
        
        bpy.ops.object.editmode_toggle()
        #we like working with tris's, faces are silly, just like yours :P
        bpy.ops.mesh.quads_convert_to_tris() 
        bpy.ops.object.editmode_toggle()
        
        #vertex color specific stuff
        b_faces = [(4,0,3),#0
                   (4,3,7),#1
                   (2,6,7),#2
                   (2,7,3),#3
                   (1,5,2),#4
                   (5,6,2),#5
                   (0,4,1),#6
                   (4,5,1),#7
                   (4,7,5),#8
                   (7,6,5),#9
                   (0,1,2),#10
                   (0,2,3)]#11
        
        #nif mapping to base, might be useful
        n_faces = [(0,1,2),
                   (0,2,3),
                   (4,5,6),
                   (4,6,7),
                   (0,4,7),
                   (0,7,1),
                   (1,7,6),
                   (1,6,2),
                   (2,6,5),
                   (2,5,3),
                   (4,0,3),
                   (4,3,5)]
        
        vertcol = [(1.0,0.0,0.0), #r
                   (0.0,1.0,0.0), #g
                   (0.0,0.0,1.0), #b
                   (0.0,0.0,0.0), #0
                   (1.0,0.0,0.0), #r
                   (0.0,1.0,0.0), #G
                   (0.0,0.0,1.0), #b
                   (0.0,0.0,0.0)] #0
                
        bpy.ops.mesh.vertex_color_add()
        b_obj.data.vertex_colors[0].name = "VertexColor"
        
        #iterate over each face, then set the vert color through lookup, 
        for face_index, face in enumerate(b_faces): #nif_faces: 0-11 
            for vert_index, n_vert in enumerate(face): #nif_verts: 0-7

                if(vert_index == 0):
                    b_obj.data.vertex_colors["VertexColor"].data[face_index].color1.r = vertcol[n_vert][0]
                    b_obj.data.vertex_colors["VertexColor"].data[face_index].color1.g = vertcol[n_vert][1]
                    b_obj.data.vertex_colors["VertexColor"].data[face_index].color1.b = vertcol[n_vert][2]
                    
                elif(vert_index == 1):
                    b_obj.data.vertex_colors["VertexColor"].data[face_index].color2.r = vertcol[n_vert][0]
                    b_obj.data.vertex_colors["VertexColor"].data[face_index].color2.g = vertcol[n_vert][1]
                    b_obj.data.vertex_colors["VertexColor"].data[face_index].color2.b = vertcol[n_vert][2]
                    
                else:
                    b_obj.data.vertex_colors["VertexColor"].data[face_index].color3.r = vertcol[n_vert][0]
                    b_obj.data.vertex_colors["VertexColor"].data[face_index].color3.g = vertcol[n_vert][1]
                    b_obj.data.vertex_colors["VertexColor"].data[face_index].color3.b = vertcol[n_vert][2]
        
        '''            
        bpy.ops.wm.save_mainfile(filepath="test/userblend/" + self.n_name)
        '''
        return b_obj
        
    def b_check_object(self, b_obj):
        print("COMPARING BLENDER DATA")
        b_mesh = b_obj.data
        b_meshcolorlayer = b_obj.data.vertex_colors[0]
        nose.tools.assert_equal(b_meshcolorlayer.name, "VertexColoR")
        n_geom = n_data.roots[0].children[0]
        
    def n_check_data(self, n_data):
        print("COMPARING NIF DATA")
        
        
    def b_check_vert(self):
        print("Sub Check: Vertex color comparison")