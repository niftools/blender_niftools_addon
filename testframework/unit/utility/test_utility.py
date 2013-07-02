import nose
from nose import with_setup

import pyffi
from pyffi.formats.nif import NifFormat

import io_scene_nif
from io_scene_nif.utility import utilities

import bpy
import mathutils
import math

'''

'''
class Test_Utilites:

    @classmethod
    def setUpClass(cls):
        print("Setup" + str(cls))
        
        cls.build_matices(cls)
        
        cls.niBlock = NifFormat.NiNode()
        cls.niBlock.set_transform(cls.n_mat)
        
        
    def build_matices(cls):
        translation = (2.0, 3.0, 4.0)
        scale = 2
        rhsrotation = (1.0, 0.0, 0.0, 0.0, 0.866, 0.5, 0.0, -0.5, 0.866)
        
        n_vec3 = NifFormat.Vector3()
        n_vec3.x = translation[0]
        n_vec3.y = translation[1]
        n_vec3.z = translation[2]

        n_mat33 = NifFormat.Matrix33()
        n_mat33.m_11 = rhsrotation[0]
        n_mat33.m_12 = rhsrotation[1]
        n_mat33.m_13 = rhsrotation[2]
        n_mat33.m_21 = rhsrotation[3]
        n_mat33.m_22 = rhsrotation[4]
        n_mat33.m_23 = rhsrotation[5]
        n_mat33.m_31 = rhsrotation[6]
        n_mat33.m_32 = rhsrotation[7]
        n_mat33.m_33 = rhsrotation[8]
        
        
        cls.n_mat = NifFormat.Matrix44()
        cls.n_mat.set_scale_rotation_translation(scale, n_mat33, n_vec3)
        
        #create equivilant Blender matrix
        b_loc_vec = mathutils.Vector(translation)
        b_loc_vec = mathutils.Matrix.Translation(b_loc_vec)
        b_rot_mat = mathutils.Matrix.Rotation(math.radians(30.0), 4, 'X') 
        b_scale_mat = mathutils.Matrix.Scale(scale, 4)
        cls.b_mat = b_loc_vec * b_rot_mat * b_scale_mat
        
        print("Building Matrices")
        print("Nif - RHS")
        print(cls.n_mat)
        print("Blender - LHS")
        print(cls.b_mat)
        
    @classmethod
    def tearDownClass(cls):
        print("Teardown" + str(cls))
        cls.niBlock = None
        cls.vec = None
        
    def test_import_translation_matrix(self):
        converted_mat = utilities.import_matrix(self, self.niBlock)
        
        print("Comparing Matrices:")
        for row in range(0,4):
            for col in range(0,4):
                nose.tools.assert_true(converted_mat[row][col] - self.b_mat[row][col] 
                                         < NifFormat.EPSILON)
       
        
