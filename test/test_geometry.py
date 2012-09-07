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
        
        b_rot_mat_x = mathutils.Matrix.Rotation(math.radians(30.0), 4, 'X') 
        b_rot_mat_y = mathutils.Matrix.Rotation(math.radians(60.0), 4, 'Y')
        b_rot_mat_z = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')        
        b_rot_mat = b_rot_mat_x * b_rot_mat_y * b_rot_mat_z
        
        b_scale_mat = mathutils.Matrix.Scale(2, 4)
        b_transform_mat = b_trans_mat * b_rot_mat * b_scale_mat
        return b_transform_mat
    
    def b_create_objects(self):
        
        bpy.ops.mesh.primitive_cube_add()      
        b_obj = bpy.data.objects[bpy.context.active_object.name]#grab the last added object, avoids name confusion
        b_obj.name = self.b_cube
        
        #object transform
        bpy.ops.transform.resize(value=(2,1,1), constraint_axis=(True,False,False), constraint_orientation='LOCAL')#scale
        bpy.ops.object.transform_apply(scale=True)# apply scale
        
        #local transform
        b_obj.matrix_local = self.rotation_matrix()
        
        b_obj.data.show_double_sided = False # prim_cube_add sets double sided; fix this
        
        bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        
    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_cube]        

        #transforms
        b_loc_vec, b_rot_quat, b_scale_vec = b_obj.matrix_local.decompose()
        
        nose.tools.assert_equal(b_obj.location, mathutils.Vector((20.0, 20.0, 20.0))) #location
        
        b_rot_quat.to_euler()
        b_rot_eul = b_rot_quat
        nose.tools.assert_equal((b_rot_eul.x - math.radians(30.0)) < self.EPSILON, True)#x rotation
        nose.tools.assert_equal((b_rot_eul.y - math.radians(60.0)) < self.EPSILON, True)#y rotation
        nose.tools.assert_equal((b_rot_eul.z - math.radians(90.0)) < self.EPSILON, True)#z rotation
        nose.tools.assert_equal((b_obj.scale - mathutils.Vector((0.75, 0.75, 0.75))) 
                < mathutils.Vector((self.EPSILON,self.EPSILON,self.EPSILON)), True) #uniform scale
        
        b_mesh = b_obj.data
        self.b_check_geom(b_mesh)
        
    def b_check_geom(self, b_mesh):
        num_triangles = len( [face for face in b_mesh.faces if len(face.vertices) == 3]) #check for tri
        num_triangles += 2 * len( [face for face in b_mesh.faces if len(face.vertices) == 4]) #face = 2 tris
        nose.tools.assert_equal(len(b_mesh.vertices), 8)
        nose.tools.assert_equal(num_triangles, 12)

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_is_instance(n_geom, NifFormat.NiTriShape)
        
        #check transforms
        nose.tools.assert_equal(n_geom.translation.as_tuple(),(20.0, 20.0, 20.0))#location
        
        n_rot_eul = mathutils.Matrix(n_geom.rotation.as_tuple()).to_euler()
        nose.tools.assert_equal((n_rot_eul.x - math.radians(30.0)) < self.EPSILON, True)#x rotation
        nose.tools.assert_equal((n_rot_eul.y - math.radians(60.0)) < self.EPSILON, True)#y rotation
        nose.tools.assert_equal((n_rot_eul.z - math.radians(90.0)) < self.EPSILON, True)#z rotation
        
        nose.tools.assert_equal(n_geom.scale - 0.75 < self.EPSILON, True) #scale
        
        self.n_check_geom_data(n_geom)
    
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
        '''
        b_obj = bpy.data.objects[self.b_cube]
        b_mesh = b_obj.data        
        nose.tools.assert_equal(len(b_mesh.uv_textures), 1)
        nose.tools.assert_equal()
        '''
        #TODO_3.0 - Separate out the UV writing from requiring a texture. 
        
    def n_check_data(self, n_data):
        TestBaseGeometry.n_check_data(self, n_data)
        pass
        '''
        #TODO_3.0 - See above
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

