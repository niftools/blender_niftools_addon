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
    
    #DirectX
    #[  0][  1][  2][  3] [  4][  5][  6][  7] [  8][  9][ 10][ 11] [ 12][ 13][ 14][ 15] Array:
    #[m11][m21][m31][m41] [m12][m22][m32][m42] [m13][m23][m33][m43] [m14][m24][m34][m44] Access:
    #[ s1][ r1][ r2][ t2] [ r3][ s2][ r4][ t2] [ r5][ s3][ r6][ t3] [   ][ s4][ r ][ t4] Repr:
    
    
    #Array               Access                  Representation
    #[ 0][ 4][ 8][12]    [m11][m12][m13][m14]    [s1][r3][r5][  ]    
    #[ 1][ 5][ 9][13]    [m21][m22][m23][m24]    [r1][s2][r6][  ]    
    #[ 2][ 6][10][14]    [m31][m32][m33][m34]    [r2][r4][s3][  ]    
    #[ 3][ 7][11][15]    [m41][m42][m43][m44]    [t1][t2][t3][t4]  
    
    #OpenGL
    #[ 0][ 1][ 2][ 3] [ 4][ 5][ 6][ 7] [ 8][ 9][10][11] [12][13][14][15] Array:
    #[ 1][ 2][ 3][ 4] [ 5][ 6][ 7][ 8] [ 9][10][11][12] [13][14][15][16] Access:
    #[s1][ 1][ 2][  ] [ 4][s2][ 6][  ] [ 8][ 9][s3][  ] [ x][ y][ z][ w] Repr:
    
    #OpenGL/Blender
    #[ 0][ 4][ 8][12]    [ 0][ 4][ 8][12]        [s1][ 4][ 8][ x]
    #[ 1][ 5][ 9][13]    [ 1][ 5][ 9][13]        [ 1][s2][ 9][ y]
    #[ 2][ 6][10][14]    [ 2][ 6][10][14]        [ 2][ 6][s3][ z]
    #[ 3][ 7][11][15]    [ 3][ 7][11][15]        [  ][  ][  ][ w]
    
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
        
        #print(b_rot_mat_x)
        
        cls.n_mat33 = NifFormat.Matrix33()
        
        
        cls.n_mat = NifFormat.Matrix44()
        cls.n_mat.set_translation(cls.n_vec3)
        
        cls.n_mat.m_11
        print((cls.n_mat.m_11, cls.n_mat.m_21, cls.n_mat.m_31, cls.n_mat.m_41))
        print((cls.n_mat.m_12, cls.n_mat.m_22, cls.n_mat.m_32, cls.n_mat.m_42))
        print((cls.n_mat.m_13, cls.n_mat.m_23, cls.n_mat.m_33, cls.n_mat.m_43))
        print((cls.n_mat.m_14, cls.n_mat.m_24, cls.n_mat.m_44, cls.n_mat.m_44))
        #cls.n_mat.set_scale_rotation_translation(cls.scale, 
        #                                         cls.rotation, 
        #                                         cls.translation)
        
#         print("Building Matrix")
#         print(cls.n_mat.as_tuple())
        
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
        
        
