"""Export and import meshes with material."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import b_gen_geometry
from test.geometry.trishape import n_gen_geometry
from test.collisions.bhkshape import b_gen_collision
from test.collisions.bhkshape import n_gen_collision
from test.collisions.bhkshape.bhkboxshape import b_gen_bhkboxshape
from test.collisions.bhkshape.bhkboxshape import n_gen_bhkboxshape

class TestCollisionBhkBoxShape(SingleNif):
    """Test material property"""
    
    n_name = 'collisions/bhkboxshape/test_boxshape'
    b_name = 'Cube'
    b_col_name = 'box'

    def b_create_objects(self):
        '''Create a cube and bhkboxshape collision object'''
        
        #Mesh obj
        b_obj = b_gen_geometry.b_create_base_geometry(self.b_name)
                
        #Col obj
        b_col_obj = b_gen_geometry.b_create_cube(self.b_col_name)
        b_gen_geometry.b_scale_object()
        b_col_obj.matrix_local = b_gen_geometry.b_get_transform_matrix()
        b_gen_collision.b_create_default_collision_properties(b_col_obj)
        b_gen_bhkboxshape.b_create_bhkboxshape_properties(b_col_obj)
        
        
    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_geometry.b_check_geom_obj(b_obj)
        
        b_col_obj = bpy.data.objects[self.b_col_name]
        b_gen_collision.b_check_default_collision_properties(b_col_obj)
        b_gen_bhkboxshape.b_check_bhkboxshape_properties(b_col_obj)
    
    
    def n_create_data(self):
        gen_data.n_create_header(self.n_data)
        n_gen_geometry.n_create_blocks(self.n_data)
        
        n_ninode = self.n_data.roots[0]
        n_gen_collision.n_attach_bsx_flag(n_ninode)
        
        #generate common collision tree
        n_bhkcolobj = n_gen_collision.n_attach_bhkcollisionobject(n_ninode)
        n_bhkrigidbody = n_gen_collision.n_attach_bhkrigidbody(n_bhkcolobj)
        
        #generate bhkboxshape specific data
        n_gen_bhkboxshape.n_update_bhkrigidbody(n_bhkrigidbody)
        n_bhktransform = n_gen_bhkboxshape.n_attach_bhkconvextransform(n_bhkrigidbody)
        n_gen_bhkboxshape.n_attach_bhkboxshape(n_bhktransform)
        
        return self.n_data


    def n_check_data(self):
        n_ninode = self.n_data.roots[0]
        
        #bsx flag
        # nose.tools.assert_equal(n_ninode.num_extra_data_list, 2) #UPB TODO
        n_bsxflag = n_ninode.extra_data_list[0]
        n_gen_collision.n_check_bsx_flag(n_bsxflag)
        
        #check common collision
        n_bhkcollisionobject = n_gen_collision.n_check_bhkcollisionobject_data(n_ninode)
        n_bhkrigidbody =  n_gen_collision.n_check_bhkrigidbody_data(n_bhkcollisionobject)
        
        #check bhkboxshape specific data
        n_gen_bhkboxshape.n_check_bhkrigidbody_data(n_bhkrigidbody)
        n_bhktransform = n_gen_bhkboxshape.n_check_bhkconvextransform_data(n_bhkrigidbody)
        n_gen_bhkboxshape.n_check_bhkboxshape_data(n_bhktransform)
        
        #geometry
        n_trishape = n_ninode.children[0]
        n_gen_geometry.n_check_trishape(n_trishape)
        
        