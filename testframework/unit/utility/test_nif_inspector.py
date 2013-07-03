import nose
import os
import math

import pyffi
from pyffi.formats.nif import NifFormat
from pyffi.utils.withref import ref

import mathutils



'''Handy class for reading / writing nifs'''
class Test_NifInspector:
    
    @classmethod
    def setupClass(cls):
        #dir to read from/write from eg "C:\\Users\\admin\\Desktop\\
        cls.dir = ''
        cls.filename = 'test'
        cls.data = NifFormat.Data()
        print("setup class")
    
    def test_runner(self):
        print("test running")
        self.write_file()
        self.read_file()
        pass
     
     
    def write_file(self):       
        
        self.create_data()
        print(self.data)
        with open(self.dir + self.filename + ".nif", 'wb') as stream:
            self.data.write(stream)
         
    def read_file(self):
        stream = open(self.dir + self.filename + ".nif", 'rb')
        self.data.read(stream)
        # write inspection code.
         
    def create_data(self):
        
        translation = (2.0, 3.0, 4.0)
        scale = 2
         
        #create equivilant Blender matrix
        b_loc_vec = mathutils.Vector(translation)
        b_loc_vec = mathutils.Matrix.Translation(b_loc_vec)
         
        b_rot_mat_x = mathutils.Matrix.Rotation(math.radians(30.0), 4, 'X')
        b_rot_mat_y = mathutils.Matrix.Rotation(math.radians(60.0), 4, 'Y')
        b_rot_mat_z = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')
        b_rot_mat = b_rot_mat_x * b_rot_mat_y * b_rot_mat_z
         
        b_scale_mat = mathutils.Matrix.Scale(scale, 4)
         
        b_mat = b_loc_vec * b_rot_mat * b_scale_mat
        b_mat = b_mat.transposed()
         
        self.data.version = 0x14000005
        self.data.user_version = 11
        self.data.user_version_2 = 11
        
        n_ninode_1 = NifFormat.NiNode()
        self.data.roots = [n_ninode_1]
    
        with ref(n_ninode_1) as n_ninode:
            n_ninode.name = b'Scene Root'
            n_ninode.flags = 14
            with ref(n_ninode.rotation) as n_matrix33:
                n_matrix33.m_11 = b_mat[0][0]
                n_matrix33.m_21 = b_mat[1][0]
                n_matrix33.m_31 = b_mat[2][0]
                n_matrix33.m_12 = b_mat[0][1]
                n_matrix33.m_22 = b_mat[1][1]
                n_matrix33.m_32 = b_mat[2][1]
                n_matrix33.m_13 = b_mat[0][2]
                n_matrix33.m_23 = b_mat[1][2]
                n_matrix33.m_33 = b_mat[2][2]
            
            with ref(n_ninode.translation) as n_vector3:
                n_vector3.x = b_mat[3][0]
                n_vector3.y = b_mat[3][1]
                n_vector3.z = b_mat[3][2]
            
            n_ninode.scale = 1
            
    
    