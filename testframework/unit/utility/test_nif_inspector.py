import nose
import os
import math

import pyffi
from pyffi.formats.nif import NifFormat
from pyffi.utils.withref import ref

import mathutils
import io_scene_nif
from io_scene_nif.utility import nif_utils


'''Handy class for reading / writing nifs'''
class TestNifInspector:
    
    @classmethod
    def setupClass(cls):
        #dir to read from/write from eg "C:\\Users\\admin\\Desktop\\
        cls.output_dir = 'C:\\Users\\monkey\\Desktop'
        cls.input_dir = 'C:\\Users\\monkey\\Desktop'
        cls.input_filename = 'test'
        cls.output_filename = 'test'
        cls.data = NifFormat.Data()
        print("setup class")
    
    def test_runner(self):
        print("test running")
        self.write_file()
        self.read_file()
        pass
     
     
    def write_file(self):       
        
        self.create_data()
        path = self.output_dir + self.output_filename + ".nif"
        print("Writing to: " + path)
        with open(path, 'wb') as stream:
            self.data.write(stream)
        
            
         
    def read_file(self):
        path = self.input_dir + self.input_filename + ".nif"
        stream = open(path, 'rb')
        self.data.read(stream)
        self.check_data()
         
    def create_data(self):
        print("creating data")
#         translation = (1, 2, 3)
#         scale = 2
# 
#         n_rot_mat_x = mathutils.Matrix.Rotation(math.radians(30.0), 4, 'X')
#         n_rot_mat_y = mathutils.Matrix.Rotation(math.radians(60.0), 4, 'Y')
#         n_rot_mat_z = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')
#         n_rot_mat = n_rot_mat_z * n_rot_mat_y * n_rot_mat_x
#         n_rot_mat.transpose()
#         print(n_rot_mat)
#         
#         self.data.version = 0x14000005
#         self.data.user_version = 11
#         self.data.user_version_2 = 11
#         
#         n_ninode_1 = NifFormat.NiNode()
#         self.data.roots = [n_ninode_1]
#     
#         with ref(n_ninode_1) as n_ninode:
#             n_ninode.name = b'Scene Root'
#             n_ninode.flags = 14
#             with ref(n_ninode.rotation) as n_matrix33:
#                 n_matrix33.m_11 = n_rot_mat[0][0]
#                 n_matrix33.m_21 = n_rot_mat[0][1]
#                 n_matrix33.m_31 = n_rot_mat[0][2]
#                 n_matrix33.m_12 = n_rot_mat[1][0]
#                 n_matrix33.m_22 = n_rot_mat[1][1]
#                 n_matrix33.m_32 = n_rot_mat[1][2]
#                 n_matrix33.m_13 = n_rot_mat[2][0]
#                 n_matrix33.m_23 = n_rot_mat[2][1]
#                 n_matrix33.m_33 = n_rot_mat[2][2]
#             print(n_matrix33)
#             with ref(n_ninode.translation) as n_vector3:
#                 n_vector3.x = translation[0]
#                 n_vector3.y = translation[1]
#                 n_vector3.z = translation[2]
#             
#             n_ninode.scale = scale
            
            
    def check_data(self):
        print("Checking data")
#         ni_node = self.data.roots[0]
#         b_mat = nif_utils.import_matrix(ni_node)
#         print(b_mat)
        
    