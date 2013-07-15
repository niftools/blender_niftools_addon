import nose

import pyffi
from pyffi.formats.nif import NifFormat

import io_scene_nif
from io_scene_nif.utility import nif_utils

import bpy
import mathutils
import math

class Test_Utilites:
#Read docs/development/issues.rst for more info on matrix conversions.

    @classmethod
    def setUpClass(cls):
        print("Setup" + str(cls))
        
        cls.build_matices(cls)
        
        cls.niBlock = NifFormat.NiNode()
        cls.niBlock.set_transform(cls.n_mat)
        
        
    def build_matices(cls):
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
        
        n_vec3 = NifFormat.Vector3()
        n_vec3.x = translation[0]
        n_vec3.y = translation[1]
        n_vec3.z = translation[2]

        n_mat33_x = NifFormat.Matrix33()
        n_mat33_x.m_11 = rhsrotx[0]
        n_mat33_x.m_12 = rhsrotx[1]
        n_mat33_x.m_13 = rhsrotx[2]
        n_mat33_x.m_21 = rhsrotx[3]
        n_mat33_x.m_22 = rhsrotx[4]
        n_mat33_x.m_23 = rhsrotx[5]
        n_mat33_x.m_31 = rhsrotx[6]
        n_mat33_x.m_32 = rhsrotx[7]
        n_mat33_x.m_33 = rhsrotx[8]
        
        n_mat33_y = NifFormat.Matrix33()
        n_mat33_y.m_11 = rhsroty[0]
        n_mat33_y.m_12 = rhsroty[1]
        n_mat33_y.m_13 = rhsroty[2]
        n_mat33_y.m_21 = rhsroty[3]
        n_mat33_y.m_22 = rhsroty[4]
        n_mat33_y.m_23 = rhsroty[5]
        n_mat33_y.m_31 = rhsroty[6]
        n_mat33_y.m_32 = rhsroty[7]
        n_mat33_y.m_33 = rhsroty[8]
        
        n_mat33_z = NifFormat.Matrix33()
        n_mat33_z.m_11 = rhsrotz[0]
        n_mat33_z.m_12 = rhsrotz[1]
        n_mat33_z.m_13 = rhsrotz[2]
        n_mat33_z.m_21 = rhsrotz[3]
        n_mat33_z.m_22 = rhsrotz[4]
        n_mat33_z.m_23 = rhsrotz[5]
        n_mat33_z.m_31 = rhsrotz[6]
        n_mat33_z.m_32 = rhsrotz[7]
        n_mat33_z.m_33 = rhsrotz[8]
        
        n_com = n_mat33_x * n_mat33_y * n_mat33_z
        
        cls.n_mat = NifFormat.Matrix44()
        cls.n_mat.set_scale_rotation_translation(scale, n_com, n_vec3)
        
        #create equivilant Blender matrix
        b_loc_vec = mathutils.Vector(translation)
        b_loc_vec = mathutils.Matrix.Translation(b_loc_vec)
        
        b_rot_mat_x = mathutils.Matrix.Rotation(math.radians(30.0), 4, 'X')
        b_rot_mat_y = mathutils.Matrix.Rotation(math.radians(60.0), 4, 'Y')
        b_rot_mat_z = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')
        b_rot_mat = b_rot_mat_z * b_rot_mat_y * b_rot_mat_x
        
        b_scale_mat = mathutils.Matrix.Scale(scale, 4)
        
        cls.b_mat = b_loc_vec * b_rot_mat * b_scale_mat
        
        print("Building Matrices")
        print("Nif - LHS")
        print(cls.n_mat)
        print("Blender - RHS")
        print(cls.b_mat)
        
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
                      str(converted_mat[row][col]) + " : " + str(self.b_mat[row][col]))
                nose.tools.assert_true(converted_mat[row][col] - self.b_mat[row][col] 
                                         < NifFormat.EPSILON)
       
        
