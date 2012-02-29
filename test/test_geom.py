"""Exports and imports mesh data"""

import bpy
import nose.tools

from test import SingleNif
from test import Base
from pyffi.formats.nif import NifFormat

class TestBaseGeom(SingleNif):
    n_name = "geom/base_geom"
    b_name = "Cube"

    def b_create_object(self):
        # note: primitive_cube_add creates object named "Cube"
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects["Cube"]
        # primitive_cube_add creates a double sided mesh; fix this
        b_obj.data.show_double_sided = False
        
        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        return b_obj

    def b_check_data(self, b_obj):
        b_mesh = b_obj.data
        
        
    def b_check_geom(self, b_obj):
        num_triangles = len(
            [face for face in b_mesh.faces if len(face.vertices) == 3])
        num_triangles += 2 * len(
            [face for face in b_mesh.faces if len(face.vertices) == 4])
        nose.tools.assert_equal(len(b_mesh.vertices), 8)
        
        nose.tools.assert_equal(num_triangles, 12)

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_is_instance(n_geom, NifFormat.NiTriShape)
    
    def n_check_geom_data(self, n_geom):
        
        nose.tools.assert_equal(n_geom.data.num_vertices, 8)
        nose.tools.assert_equal(n_geom.data.num_triangles, 12)
        
    '''
        TODO: Additional checks needed.
        TriData
            Flags: blender exports| Continue, Maya| Triangles, Pyffi| Bound.
            Consistancy:
            radius:
    '''
        
class TestBaseUV(TestBaseGeom):
    n_name = "geom/base_uv"
    
    def b_create_object(self):
        b_obj = TestBaseGeom.b_create_object(self)
        
        #project UV
        bpy.ops.object.mode_set(mode='EDIT', toggle=False) #ensure we are in the mode.
        bpy.ops.uv.cube_project() # named 'UVTex'
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        
        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        return b_obj
    
    def b_check_data(self, b_obj):
        TestBaseGeom.b_check_data(self, b_obj)
        pass
        '''
        TODO_3.0 - Separate out the UV writing from requiring a texture. 
            b_mesh = b_obj.data        
            nose.tools.assert_equal(len(b_mesh.uv_textures), 1)
            nose.tools.assert_equal()
        '''
    
    def n_check_data(self, n_data):
        TestBaseGeom.n_check_data(self, n_data)
        pass
        '''
        TODO_3.0 - See above
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(len(n_geom.data.uv_sets), 1)
        nose.tools.assert_equal(len(n_geom.data.uv_sets[0]), len(n_geom.data.vertices))
        '''

class TestNonUniformlyScaled(Base):
    def setup(self):
        # create a non-uniformly scaled cube
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects["Cube"]
        b_obj.scale = (1, 2, 3)

    @nose.tools.raises(Exception)
    def test_export(self):
        bpy.ops.export_scene.nif(
            filepath="test/export/non_uniformly_scaled_cube.nif",
            log_level='DEBUG',
            )

