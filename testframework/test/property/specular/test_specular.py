"""Export and import meshes with specular values."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import b_gen_geometry
from test.geometry.trishape import n_gen_geometry
from test.property.material import b_gen_material
from test.property.material import n_gen_material
from test.property.specular import b_gen_specular
from test.property.specular import n_gen_specular

class TestSpecularProperty(SingleNif):
    """Test import/export of meshes with material based alpha property."""
    
    n_name = "property/specular/base_specular"
    b_name = "Cube"
    
    def b_create_objects(self):
        b_obj = b_gen_geometry.b_create_base_geometry(self.b_name)
        b_mat = b_gen_material.b_create_material_block(b_obj)
        b_gen_material.b_create_set_material_property(b_mat)
        b_gen_specular.b_create_specular_property(b_mat) # update specular

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_geometry.b_check_geom_obj(b_obj)
        b_mat = b_gen_material.b_check_material_block(b_obj)
        b_gen_specular.b_check_specular_property(b_mat)

    def n_create_data(self):
        gen_data.n_create_header(self.n_data)
        n_gen_geometry.n_create_blocks(self.n_data)
        n_trishape = self.n_data.roots[0].children[0]
        n_gen_material.n_attach_material_prop(n_trishape)
        n_gen_specular.n_alter_material_specular(n_trishape.properties[0]) # set material alpha
        n_gen_specular.n_attach_specular_prop(n_trishape) # add nialphaprop
        return self.n_data

    def n_check_data(self, n_data):
        n_nitrishape = n_data.roots[0].children[0]
        n_gen_geometry.n_check_trishape(n_nitrishape)
        
        nose.tools.assert_equal(n_nitrishape.num_properties, 2) 
        n_mat_prop = n_nitrishape.properties[1]    
        n_gen_material.n_check_material_block(n_mat_prop)
        n_gen_specular.n_check_material_specular(n_mat_prop)
        
        n_specular_prop = n_nitrishape.properties[0]
        n_gen_specular.n_check_specular_block(n_specular_prop)
        n_gen_specular.n_check_specular_property(n_specular_prop)
