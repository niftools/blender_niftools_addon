"""Export and import material."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import b_gen_geometry
from test.geometry.trishape import n_gen_geometry
from test.property.material import b_gen_material
from test.property.material import n_gen_material

class TestMaterialProperty(SingleNif):
    """Test material property"""
    
    n_name = 'property/material/base_material'
    b_name = 'Cube'

    def b_create_objects(self):
        b_obj = b_gen_geometry.b_create_base_geometry(self.b_name)
        b_mat = b_gen_material.b_create_material_block(b_obj)
        b_gen_material.b_create_set_material_property(b_mat)

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_geometry.b_check_geom_obj(b_obj)
        
        b_mat = b_gen_material.b_check_material_block(b_obj)
        b_gen_material.b_check_material_property(b_mat)

    def n_create_data(self):
        gen_data.n_create_header(self.n_data)
        n_gen_geometry.n_create_blocks(self.n_data)
        
        n_trishape = self.n_data.roots[0].children[0]
        n_gen_material.n_attach_material_prop(n_trishape)
        return self.n_data

    def n_check_data(self, n_data):
        n_nitrishape = n_data.roots[0].children[0]
        n_gen_geometry.n_check_trishape(n_nitrishape)
        
        nose.tools.assert_equal(n_nitrishape.num_properties, 1) 
        n_mat_prop = n_nitrishape.properties[0]    
        n_gen_material.n_check_material_block(n_mat_prop)
        n_gen_material.n_check_material_property(n_mat_prop)

'''
class TestAmbientMaterial(TestMaterialProperty):
    n_name = "property/material/base_ambient"

    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self)
        b_mat = b_obj.data.materials[0]

        #diffuse settings
        b_mat.niftools.ambient_color = (0.0,1.0,0.0)#TODO_3.0 - update func-> World ambient
        return b_obj

    def b_check_data(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        self.b_check_ambient_property(b_mat)

    def b_check_ambient_property(self, b_mat)
        nose.tools.assert_equal(b_mat.niftools.ambient_color, (0.0,1.0,0.0))

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        self.n_check_material_property(n_geom.properties[0])

    def n_check_material_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)
        nose.tools.assert_equal(n_mat_prop.ambient_color, (0.0,1.0,0.0))

class TestDiffuseMaterial(TestMaterialProperty):
    n_name = "property/material/base_diffuse"

    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self)
        b_mat = b_obj.data.materials[0]

        #diffuse settings
        b_mat.niftools.diffuse_color = (0.0,1.0,0.0)#TODO_3.0 - update func-> World ambient
        return b_obj

    def b_check_data(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        self.b_check_diffuse_property(b_mat)

    def b_check_diffuse_property(self, b_mat)
        nose.tools.assert_equal(b_mat.niftools.diffuse_color, (0.0,1.0,0.0))
        nose.tools.assert_equal(b_mat.diffuse_intensity, 1.0)

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        self.n_check_material_property(n_geom.properties[0])

    def n_check_material_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)
        nose.tools.assert_equal(n_mat_prop.diffuse_color, (0.0,1.0,0.0))

'''
