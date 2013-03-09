"""Export and import meshes with material."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import b_gen_geometry
from test.geometry.trishape import n_gen_geometry
from test.collisions.bhkshape import b_gen_bhkboxshape
from test.collisions.bhkshape import n_gen_bhkboxshape

class TestCollisionBhkBoxShape(SingleNif):
    """Test material property"""
    
    n_name = 'collision/bhkboxshape/test_boxshape'
    b_name = 'Cube'
    b_col_name = 'Box Collision'

    def b_create_objects(self):
        '''Create a cube and bhkboxshape collision object'''
        
        #Mesh obj
        b_obj = b_gen_geometry.b_create_base_geometry(self.b_name)
        
        #Col obj
        b_col = b_gen_geometry.b_create_cube(self.b_col_name)

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_geometry.b_check_geom_obj(b_obj)


    
    def n_create_data(self):
        gen_data.n_create_header(self.n_data)
        n_gen_geometry.n_create_blocks(self.n_data)
        n_trishape = self.n_data.roots[0].children[0]
    
    
        return self.n_data

    def n_check_data(self):
        n_nitrishape = self.n_data.roots[0].children[0]
        n_gen_geometry.n_check_trishape(n_nitrishape)
        
        nose.tools.assert_equal(n_nitrishape.num_properties, 0)
        
class TestBhkCollisionBoxShape(TestBaseGeometry, TestBhkCollision):
    n_name = "collisions/base_bhkcollision_box" #name of nif
    b_name = "Cube" #name of blender mesh object

    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self)
        b_coll = TestBaseGeometry.b_create_object(self, "CollisionBox")
        b_coll.draw_type = 'WIRE'

        #Physics
        b_coll.game.use_collision_bounds = True
        b_coll.game.collision_bounds_type = 'BOX'

        b_coll.nifcollision.use_blender_properties = True
        b_coll.nifcollision.motion_system = "MO_SYS_FIXED"
        b_coll.nifcollision.oblivion_layer = "OL_STATIC"
        b_coll.nifcollision.quality_type = "MO_QUAL_FIXED"
        b_coll.nifcollision.col_filter = 0
        b_coll.nifcollision.havok_material = "HAV_MAT_WOOD"

        b_coll.select = True



