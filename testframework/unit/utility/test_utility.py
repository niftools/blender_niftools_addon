import nose
from nose.tools import nottest

import pyffi
from pyffi.formats.nif import NifFormat

import io_scene_nif
from io_scene_nif.utility import nif_utils

import bpy
import mathutils
import math

@nottest
class Test_Utilites:
#Read docs/development/issues.rst for more info on matrix conversions.

    @classmethod
    def setUpClass(cls):
        print("Setup" + str(cls))
        
        cls.nif_matrix = cls.build_nif_matrix()
        cls.niBlock = NifFormat.NiNode()
        cls.niBlock.set_transform(cls.nif_matrix)
        
        cls.blender_matrix = cls.build_blender_matrix()
        
    @classmethod
    def tearDownClass(cls):
        print("Teardown" + str(cls))
        
        cls.niBlock = None
        cls.vec = None
        
    def test_import_matrix(self):
        converted_mat = nif_utils.import_matrix(self.niBlock)
        
        print("Comparing Matrices:")
        for row in range(0,4):
            for col in range(0,4):
                print(str(row) + ":" + str(col) + " = " + 
                      str(converted_mat[row][col]) + " : " + str(self.blender_matrix[row][col]))
                nose.tools.assert_true(converted_mat[row][col] - self.blender_matrix[row][col] 
                                         < NifFormat.EPSILON)
                
                
    @classmethod
    def build_blender_matrix(cls):
        translation = (2.0, 3.0, 4.0)
        scale = 2
        
        #Blender matrix
        b_loc_vec = mathutils.Vector(translation)
        b_loc_vec = mathutils.Matrix.Translation(b_loc_vec)
        
        b_rot_mat_x = mathutils.Matrix.Rotation(math.radians(30.0), 4, 'X')
        b_rot_mat_y = mathutils.Matrix.Rotation(math.radians(60.0), 4, 'Y')
        b_rot_mat_z = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')
        b_rot_mat = b_rot_mat_x * b_rot_mat_y * b_rot_mat_z
        
        b_scale_mat = mathutils.Matrix.Scale(scale, 4)
        b_matrix = b_scale_mat * b_rot_mat * b_loc_vec 
        
        print("Blender - RHS")
        print(b_matrix)
        
        return b_matrix
    
        
    @classmethod
    def build_nif_matrix(cls):
        n_mat = NifFormat.Matrix44()
        translation = (2.0, 3.0, 4.0)
        scale = 2
        rhsrotx = (1.0, 0.0, 0.0,
                   0.0, 0.866, 0.5,
                   0.0, -0.5, 0.866)
        
        rhsroty = (0.5, 0.0, -0.866,
                   0.0, 1.0, 0.0,
                   0.866, 0.0, 0.5)
        
        rhsrotz = (0, 1, 0,
                   -1, 0, 0,
                   0, 0, 1)
        
        rhsrot = (0, -0.8660, 0.5,
                  0.5,  0.4330, 0.75,
                  -0.8660, 0.2550, 0.4330)
        
        n_vec3 = NifFormat.Vector3()
        n_vec3.x = translation[0]
        n_vec3.y = translation[1]
        n_vec3.z = translation[2]

        n_mat33 = NifFormat.Matrix33()
        n_mat33.m_11 = rhsrotx[0]
        n_mat33.m_12 = rhsrotx[3]
        n_mat33.m_13 = rhsrotx[6]
        n_mat33.m_21 = rhsrotx[1]
        n_mat33.m_22 = rhsrotx[4]
        n_mat33.m_23 = rhsrotx[7]
        n_mat33.m_31 = rhsrotx[2]
        n_mat33.m_32 = rhsrotx[5]
        n_mat33.m_33 = rhsrotx[8]
        

        n_mat.set_scale_rotation_translation(scale, n_mat33, n_vec3)
        
        print("Building Matrices")
        print("Nif - LHS")
        print(n_mat)
        
        return n_mat