"""Export and import material meshes with emissive materials."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import gen_geometry
from test.geometry.trishape.test_geometry import TestBaseGeometry
from test.property.material import gen_material
from test.property.material.test_material import TestMaterialProperty


class TestEmissiveMaterial(SingleNif):
    """Test import/export of meshes with material emissive property."""
    
    n_name = "property/material/base_emissive"
    b_name = 'Cube'

    def b_create_objects(self):
        b_obj = TestBaseGeometry.b_create_base_geometry()
        
        # setup material
        b_obj.name = self.b_name
        TestMaterialProperty.b_create_material_block(b_obj)      
        b_mat = b_obj.data.materials[0]
        TestMaterialProperty.b_create_set_material_property(b_mat)
        
        self.b_create_emmisive_property(b_mat) # set our emissive value
    
    @classmethod
    def b_create_emmisive_property(cls, b_mat):
        b_mat.niftools.emissive_color = (0.5,0.0,0.0)
        b_mat.emit = 1.0
        return b_mat

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        TestBaseGeometry.b_check_geom_obj(b_obj)
        TestMaterialProperty.b_check_material_block(b_obj)
        
        b_mat = b_obj.data.materials[0]
        self.b_check_emission_property(b_mat)

    @classmethod
    def b_check_emission_property(cls, b_mat):
        nose.tools.assert_equal(b_mat.emit, 1.0)
        nose.tools.assert_equal((b_mat.niftools.emissive_color.r,
                                 b_mat.niftools.emissive_color.g,
                                 b_mat.niftools.emissive_color.b),
                                (0.5,0.0,0.0))

    def n_create_data(self):
        gen_data.n_create_data(self.n_data)
        gen_geometry.n_create_blocks(self.n_data)
        
        n_trishape = self.n_data.roots[0].children[0]
        gen_material.n_attach_material_prop(n_trishape)
        gen_material.n_alter_emissive(n_trishape.properties[0])
        return self.n_data


    def n_check_data(self, n_data):
        n_nitrishape = n_data.roots[0].children[0]
        TestBaseGeometry.n_check_trishape(n_nitrishape)

        # check we have property and correct type
        nose.tools.assert_equal(n_nitrishape.num_properties, 1)
        n_mat_prop = n_nitrishape.properties[0]        
        TestMaterialProperty.n_check_material_block(n_mat_prop)
        
        # check its values
        self.n_check_material_emissive_property(n_mat_prop)
        
    @classmethod
    def n_check_material_emissive_property(cls, n_mat_prop):
        nose.tools.assert_equal((n_mat_prop.emissive_color.r,
                                 n_mat_prop.emissive_color.g,
                                 n_mat_prop.emissive_color.b),
                                (0.5,0.0,0.0))
