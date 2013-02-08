"""Export and import meshes with material based alpha values."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import gen_geometry
from test.geometry.trishape.test_geometry import TestBaseGeometry
from test.property.material import gen_material
from test.property.material.test_material import TestMaterialProperty
from test.property.alpha import gen_alpha


class TestAlphaProperty(SingleNif):
    """Test import/export of meshes with material based alpha property."""
    
    n_name = "property/alpha/base_alpha"
    b_name = "Cube"
    
    def b_create_objects(self):
        b_obj = TestBaseGeometry.b_create_base_geometry()
        b_obj.name = self.b_name
        
        # setup basic material
        TestMaterialProperty.b_create_material_block(b_obj)
        b_mat = b_obj.data.materials[0]
        TestMaterialProperty.b_create_set_material_property(b_mat)
        
        # update alpha
        self.b_create_set_alpha_property(b_mat)

    @classmethod
    def b_create_set_alpha_property(cls, b_mat):
        b_mat.use_transparency = True
        b_mat.alpha = 0.5
        b_mat.transparency_method = 'Z_TRANSPARENCY'

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        TestBaseGeometry.b_check_geom_obj(b_obj)
        
        TestMaterialProperty.b_check_material_block(b_obj)
        b_mat = b_obj.data.materials[0]
        TestMaterialProperty.b_check_material_property(b_mat)
        self.b_check_alpha_property(b_mat)

    @classmethod
    def b_check_alpha_property(cls, b_mat):
        '''Check alpha related properties'''
        nose.tools.assert_equal(b_mat.use_transparency, True)
        nose.tools.assert_equal(b_mat.alpha, 0.5)
        nose.tools.assert_equal(b_mat.transparency_method, 'Z_TRANSPARENCY')

    def n_create_data(self):
        self.n_data = gen_data.n_create_data(self.n_data)
        self.n_data = gen_geometry.n_create_blocks(self.n_data)
        
        n_trishape = self.n_data.roots[0].children[0]
        gen_material.n_attach_material_prop(n_trishape)
        gen_alpha.n_alter_material_alpha(n_trishape.properties[0])
            
        gen_alpha.n_attach_alpha_prop(n_trishape)
        
        return self.n_data

    def n_check_data(self, n_data):
        n_trishapedata = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_trishapedata.num_properties, 2)
        
        n_mat_prop = n_trishapedata.properties[1]
        self.n_check_material_alpha(n_mat_prop)
        
        n_alpha_prop = n_trishapedata.properties[0]
        self.n_check_alpha_block(n_alpha_prop)
        self.n_check_alpha_property(n_alpha_prop)
        
    @classmethod
    def n_check_material_alpha(cls, n_mat_prop):
        '''Check that material has correct alpha value'''
        nose.tools.assert_equal(n_mat_prop.alpha, 0.5)

    @classmethod
    def n_check_alpha_block(cls, n_alpha_prop):
        '''Check that block is actually NiAlphaProperty'''
        nose.tools.assert_is_instance(n_alpha_prop, NifFormat.NiAlphaProperty)
    
    @classmethod
    def n_check_alpha_property(cls, n_alpha_prop):
         '''Check NiAlphaProperty values'''
         nose.tools.assert_equal(n_alpha_prop.flags, 4845) # Ref: gen_alpha for values
         nose.tools.assert_equal(n_alpha_prop.threshold, 0)

         
        
        