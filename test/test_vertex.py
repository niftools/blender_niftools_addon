"""Exports and imports vertex color"""

import bpy
import nose.tools
import os

import io_scene_nif.nif_export
from pyffi.formats.nif import NifFormat
from test.test_geometry import TestBaseGeometry

class TestBaseVertexColor(TestBaseGeometry):
    n_name = "geometry/vertexcolor/base_vertex_color"
    b_name = "Cube"
    
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
    
        
    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self)
        
        #we like working with tris's, quad faces are silly, just like yours :P
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.quads_convert_to_tris() 
        bpy.ops.object.editmode_toggle()
        
        #add base vertex col layer
        bpy.ops.mesh.vertex_color_add()
        b_obj.data.vertex_colors[0].name = "VertexColor"
        
        #iterate over each face, then set the vert color through lookup, 
        for face_index, face in enumerate(self.b_faces): #nif_faces: 0-11 
            for vert_index, n_vert in enumerate(face): #nif_verts: 0-7
                b_meshcolor = b_obj.data.vertex_colors["VertexColor"].data[face_index]
                b_color = getattr(b_meshcolor, "color%s" % (vert_index + 1))
                b_color.r = self.vertcol[n_vert][0]
                b_color.g = self.vertcol[n_vert][1]
                b_color.b = self.vertcol[n_vert][2]
        
        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)        
        return b_obj
        
    def b_check_object(self, b_obj):
        TestBaseGeometry.b_check_object(self, b_obj)
        b_mesh = b_obj.data
        nose.tools.assert_equal(len(b_mesh.vertex_colors), 1)
        nose.tools.assert_equal(b_mesh.vertex_colors[0].name, 'VertexColor')
        b_meshcolor = b_obj.data.vertex_colors["VertexColor"].data
        for b_col_index, b_meshcolor in enumerate(b_meshcolor): #b_faces: 0-11          
            self.b_check_vert(b_col_index, b_meshcolor)
                
    def b_check_vert(self, f_index, vertexcolor):
        for vert_index in [0,1,2]:
            b_color = getattr(vertexcolor, "color%s" % (vert_index + 1))
            nose.tools.assert_equal(b_color.r == self.vertcol[f_index][0], True)
            nose.tools.assert_equal(b_color.g == self.vertcol[f_index][1], True)
            nose.tools.assert_equal(b_color.b == self.vertcol[f_index][2], True)
    
    def n_check_data(self, n_data):
        TestBaseGeometry.n_check_data(self, n_data)
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.data.has_vertex_colors, True)
        nose.tools.assert_equal(len(n_geom.data.vertex_colors), 8)
        for i, vert in enumerate(n_geom.data.vertex_colors):
            self.n_check_vert(i, vert)

    def n_check_vert(self, index, vertexcolor):
        print("Sub Check: Comparing vertex color")
        print("n_vert:" + str(vertexcolor.r) + " base_vert:" + str(self.vertcol[index][0]))
        nose.tools.assert_equal(abs(vertexcolor.r - self.vertcol[index][0]) > 0.01, False)
        print("n_vert:" + str(vertexcolor.g) + " base_vert:" + str(self.vertcol[index][1]))      
        nose.tools.assert_equal(abs(vertexcolor.g - self.vertcol[index][1]) > 0.01, False)
        print("n_vert:" + str(vertexcolor.b) + " base_vert:" + str(self.vertcol[index][2]))
        nose.tools.assert_equal(abs(vertexcolor.b - self.vertcol[index][2]) > 0.01, False)
        