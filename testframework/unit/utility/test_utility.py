import nose
from nose import with_setup

import pyffi
from pyffi.formats.nif import NifFormat

import io_scene_nif
from io_scene_nif.utility import utilities

import bpy
import mathutils
import math

class Test_Utilites:
    
    #On Disk:
    #[0][1][2][3][4][5][6][7][8][9][10][11][12][13][14][15]
    
    #DirectX            
    #[ 0][ 4][ 8][12]    [r]
    #[ 1][ 5][ 9][13]
    #[ 2][ 6][10][14]
    #[ 3][ 7][11][15]
    
    #OpenGL/Blender
    #[ 0][ 1][ 2][ 3]
    #[ 4][ 5][ 6][ 7]
    #[ 8][ 9][10][11]
    #[12][13][14][15]
    
    @classmethod
    def setUpClass(cls):
        print("Setup" + str(cls))
        
        cls.translation = (2.0, 3.0, 4.0)
        cls.scale = 2
        cls.rotation = ()
        
        cls.n_vec3 = NifFormat.Vector3()
        cls.n_vec3.x = cls.translation[0]
        cls.n_vec3.y = cls.translation[1]
        cls.n_vec3.z = cls.translation[2]

        
        #rotation
        b_rot_mat_x = mathutils.Matrix.Rotation(math.radians(30.0), 4, 'X') 
        #b_rot_mat_y = mathutils.Matrix.Rotation(math.radians(60.0), 4, 'Y')
        #b_rot_mat_z = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')        
        #b_rot_mat =  b_rot_mat_x * b_rot_mat_y * b_rot_mat_z
        
        print(b_rot_mat_x.inverted())
        
        cls.n_mat33 = NifFormat.Matrix33()
        
        
        cls.n_mat = NifFormat.Matrix44()
        #cls.n_mat.set_scale_rotation_translation(cls.scale, 
        #                                         cls.rotation, 
        #                                         cls.translation)
        
        print("Building Matrix")
        print(cls.n_mat.as_tuple())
        
        cls.niBlock = NifFormat.NiNode()
        cls.niBlock.set_transform(cls.n_mat)
        
    @classmethod
    def tearDownClass(cls):
        print("Teardown" + str(cls))
        cls.niBlock = None
        cls.vec = None
        
    def test_import_translation_matrix(self):
        converted_mat = utilities.import_matrix(self, self.niBlock, relative_to=None)
        
        b_mat = mathutils.Matrix.Translation((2.0, 3.0, 4.0))
        
        #nose.tools.assert_equal(converted_mat, b_mat)
        
        
