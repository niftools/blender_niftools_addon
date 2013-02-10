"""Export and import material meshes."""
"""Export and import meshes with wire materials."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import b_gen_geometry
from test.geometry.trishape import n_gen_geometry
from test.property.material import b_gen_material
from test.property.material import n_gen_material
from test.property.wireframe import b_gen_wire
from test.property.wireframe import n_gen_wire

class TestWireframeProperty(SingleNif):
    """Test import/export of meshes with material based specular property."""
    
    n_name = "property/wireframe/test_wire"
    b_name = "Cube"
    
    def b_create_objects(self):
        b_obj = b_gen_geometry.b_create_base_geometry(self.b_name)
        b_mat = b_gen_material.b_create_material_block(b_obj)
        b_gen_material.b_create_set_material_property(b_mat)
        b_gen_wire.b_create_wireframe_property(b_mat)

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_geometry.b_check_geom_obj(b_obj)
        b_mat = b_gen_material.b_check_material_block(b_obj)
        b_gen_wire.b_check_wire_property(b_mat)

    def n_create_data(self):
        gen_data.n_create_header(self.n_data)
        n_gen_geometry.n_create_blocks(self.n_data)
        n_trishape = self.n_data.roots[0].children[0]
        n_gen_material.n_attach_material_prop(n_trishape)
        n_gen_wire.n_attach_wire_prop(n_trishape) # add niwireframeprop
        return self.n_data
    
    def n_check_data(self, n_data):
        n_nitrishape = n_data.roots[0].children[0]
        n_gen_geometry.n_check_trishape(n_nitrishape)
        
        nose.tools.assert_equal(n_nitrishape.num_properties, 2)
        n_mat_prop = n_nitrishape.properties[1]    
        n_gen_material.n_check_material_block(n_mat_prop)
        
        n_wire_prop = n_nitrishape.properties[0]
        n_gen_wire.n_check_wire_property(n_wire_prop)



