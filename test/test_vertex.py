"""Exports and imports vertex color"""

import bpy
import nose.tools
import os

import io_scene_nif.export_nif
from pyffi.formats.nif import NifFormat
from test.test_cube import TestBaseCube

class TestBaseVertexColor(TestBaseCube):
    n_name = "vertexcolor/base_vertex_color"
    b_name = "Cube"
        
    def b_create_object(self):
        b_obj = TestBaseCube.b_create_object(self)
        
        #we like working with tris's, quad faces are silly, just like yours :P
        bpy.ops.object.editmode_toggle()
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
                b_meshcolor = b_obj.data.vertex_colors["VertexColor"].data[face_index]
                b_color = getattr(b_meshcolor, "color%s" % (vert_index + 1))
                b_color.r = vertcol[n_vert][0]
                b_color.g = vertcol[n_vert][1]
                b_color.b = vertcol[n_vert][2]
                
        bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        
        return b_obj
        
    def b_check_object(self, b_obj):
        print("COMPARING BLENDER DATA")
        '''
        b_meshcolorlayer = b_obj.data.vertex_colors[0]
        nose.tools.assert_equal(b_meshcolorlayer.name, 'VertexColor')
        '''
        
    def n_check_data(self, n_data):
        print("COMPARING NIF DATA")
        
        
    def b_check_vert(self):
        print("Sub Check: Per vertex color comparison")