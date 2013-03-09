"""Export and import meshes with uv data."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import b_gen_geometry
from test.geometry.trishape import n_gen_geometry
from test.geometry.uv import b_gen_uv
from test.geometry.uv import n_gen_uv
from test.property.material import b_gen_material
from test.property.material import n_gen_material

class TestBaseUV(SingleNif):
    
    b_name = 'Cube'
    n_name = "geometry/uvdata/test_uv"
    
    def b_create_objects(self):        
        b_obj = b_gen_geometry.b_create_cube(self.b_name)
        b_gen_uv.b_uv_object()
        b_gen_geometry.b_transform_cube(b_obj)
        
    
    def b_check_data(self):
        pass
        '''
        b_obj = bpy.data.objects[self.b_name]
        b_mesh = b_obj.data
        nose.tools.assert_equal(len(b_mesh.uv_textures), 1)
        nose.tools.assert_equal()
        '''
        # TODO_3.0 - Separate out the UV writing from requiring a texture.

    def n_create_data(self):
        gen_data.n_create_header(self.n_data)
        n_gen_geometry.n_create_blocks(self.n_data)
        return self.n_data

    def n_check_data(self):
        pass
        '''
        #TODO_3.0 - See above
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(len(n_geom.data.uv_sets), 1)
        nose.tools.assert_equal(len(n_geom.data.uv_sets[0]), len(n_geom.data.vertices))
        '''
