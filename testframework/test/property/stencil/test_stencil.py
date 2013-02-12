"""Export and import stencil based double sided meshes."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import b_gen_geometry
from test.geometry.trishape import n_gen_geometry
from test.property.stencil import b_gen_stencil
from test.property.stencil import n_gen_stencil


class TestStencilProperty(SingleNif):
    """Test import/export of meshes with material based alpha property."""
    
    n_name = "property/stencil/test_stencil"
    b_name = "Cube"

    def b_create_objects(self):
        b_obj = b_gen_geometry.b_create_base_geometry(self.b_name)
        b_gen_stencil.b_create_stensil_property(b_obj)

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_geometry.b_check_geom_obj(b_obj)
        b_gen_stencil.b_check_stencil_property(b_obj)

    def n_create_data(self):
        gen_data.n_create_header(self.n_data)
        n_gen_geometry.n_create_blocks(self.n_data)
        n_trishape = self.n_data.roots[0].children[0]
        n_gen_stencil.n_create_stencil_prop(n_trishape)
        return self.n_data
        
    def n_check_data(self):
        n_nitrishape = self.n_data.roots[0].children[0]
        n_gen_geometry.n_check_trishape(n_nitrishape)
        
        nose.tools.assert_equal(n_nitrishape.num_properties, 1)
        n_stencil_prop = n_nitrishape.properties[0]
        n_gen_stencil.n_check_stencil_block(n_stencil_prop)
        n_gen_stencil.n_check_stencil_property(n_stencil_prop)
    

