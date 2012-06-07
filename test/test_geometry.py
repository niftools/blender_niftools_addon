"""Exports and imports mesh data"""

import bpy
import nose.tools
import math
import mathutils

from test import Base, SingleNif
from pyffi.formats.nif import NifFormat

class TestBaseGeometry(SingleNif):
    n_name = "geometry/base_geometry"
    b_cube = "Cube"
    
    def rotation_matrix(self):
        b_trans_mat = mathutils.Matrix.Translation((20.0, 20.0, 20.0))
        b_rot_mat = mathutils.Matrix.Rotation(math.radians(45.0), 4, 'X')
        b_scale_mat = mathutils.Matrix.Scale(0.75, 4)
        b_transform_mat = b_trans_mat * b_rot_mat * b_scale_mat
        return b_transform_mat
    
    def b_create_objects(self):
        
        #grab the last added object, avoids name confusion
        bpy.ops.mesh.primitive_cube_add()      
        b_obj = bpy.data.objects[bpy.context.active_object.name]
        b_obj.name = self.b_cube
        SingleNif.b_name.append(self.b_cube) #add to new object list
        
        #add transformation
        b_obj.matrix_local = self.rotation_matrix()
        
        # primitive_cube_add sets double sided; fix this
        b_obj.data.show_double_sided = False
        
        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        
    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_cube]        

        #transfroms
        b_loc, b_rot, b_scale = b_obj.matrix_local.decompose()
        #compare location value
        nose.tools.assert_equal(b_obj.location, mathutils.Vector((20.0, 20.0, 20.0))) 
        #compare rotations, float comparison
        nose.tools.assert_equal(
                (b_rot.to_axis_angle()[1] - math.radians(45.0)) 
                < self.EPSILON, True)
        #compare scale: float comparison
        nose.tools.assert_equal(
                (b_obj.scale - mathutils.Vector((0.75, 0.75, 0.75))) 
                < mathutils.Vector((self.EPSILON,self.EPSILON,self.EPSILON)), True) 
                                
        b_mesh = b_obj.data
        self.b_check_geom(b_mesh)
        
    def b_check_geom(self, b_mesh):
        num_triangles = len(
            [face for face in b_mesh.faces if len(face.vertices) == 3]) #check for tri
        num_triangles += 2 * len(
            [face for face in b_mesh.faces if len(face.vertices) == 4]) #face = 2 tris
        nose.tools.assert_equal(len(b_mesh.vertices), 8)
        nose.tools.assert_equal(num_triangles, 12)

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_is_instance(n_geom, NifFormat.NiTriShape)
        self.n_check_geom_data(n_geom)
    
    def n_check_geom_data(self, n_geom):
        nose.tools.assert_equal(n_geom.data.num_vertices, 8)
        nose.tools.assert_equal(n_geom.data.num_triangles, 12)
        
    '''
        TODO: Additional checks needed.
        TriShape
            transforms
        
        TriData
            Flags: blender exports| Continue, Maya| Triangles, Pyffi| Bound.
            Consistancy:
            radius:
    '''
        
class TestBaseUV(TestBaseGeometry):
    n_name = "geometry/base_uv"
    b_cube = 'Cube'
    
    def b_create_object(self):
        TestBaseGeometry.b_create_objects()
        b_obj = bpy.data.objects[self.b_name]
        
        #project UV
        bpy.ops.object.mode_set(mode='EDIT', toggle=False) #ensure we are in the mode.
        bpy.ops.uv.cube_project() # named 'UVTex'
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        
        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
    
    def b_check_data(self):
        TestBaseGeometry.b_check_data(self)
        pass
        
        b_obj = bpy.data.objects[self.b_cube]
        b_mesh = b_obj.data        
        nose.tools.assert_equal(len(b_mesh.uv_textures), 1)
        nose.tools.assert_equal()
        
        #TODO_3.0 - Separate out the UV writing from requiring a texture. 
            
    
    def n_check_data(self, n_data):
        TestBaseGeometry.n_check_data(self, n_data)
        pass
        
        #TODO_3.0 - See above
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(len(n_geom.data.uv_sets), 1)
        nose.tools.assert_equal(len(n_geom.data.uv_sets[0]), len(n_geom.data.vertices))
        

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

