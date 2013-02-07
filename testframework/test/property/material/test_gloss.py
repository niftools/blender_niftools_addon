"""Export and import material meshes."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import gen_geometry
from test.geometry.trishape.test_geometry import TestBaseGeometry
from test.property.material import gen_material
from test.property.material.test_material import TestMaterialProperty

class TestGlossProperty(SingleNif):
    """Export and import material meshes with gloss."""

    n_name = "property/material/base_gloss"
    b_name = 'Cube'

    def b_create_objects(self):
        b_obj = TestBaseGeometry.b_create_base_geometry()
        b_obj = TestMaterialProperty.b_create_material_block(b_obj)
        b_obj.name = self.b_name
        
        b_mat = b_obj.data.materials[0]
        b_obj.data.materials[0] = self.b_create_gloss_property(b_mat)
        
    @classmethod
    def b_create_gloss_property(cls, b_mat):
        b_mat.specular_hardness = 100
        return b_mat

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        TestMaterialProperty.b_check_material_block(b_obj)
        TestGlossProperty.b_check_gloss_block(b_obj)

    @classmethod
    def b_check_gloss_block(cls, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        cls.b_check_gloss_property(b_mat)

    @classmethod
    def b_check_gloss_property(cls, b_mat):
        nose.tools.assert_equal(b_mat.specular_hardness, 100)

    def n_create_data(self):
        self.n_data = gen_data.n_create_data(self.n_data)
        self.n_data = gen_geometry.n_create_blocks(self.n_data)
        
        n_trishape = self.n_data.roots[0].children[0]
        self.n_data.roots[0].children[0] = gen_material.n_attach_material_prop(n_trishape)
        self.n_data.roots[0].children[0].properties[0] = gen_material.n_alter_glossiness(n_trishape.properties[0])
        return self.n_data

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        TestMaterialProperty.n_check_material_property(n_geom.properties[0])
        self.n_check_material_gloss_property(n_geom.properties[0])

    @classmethod
    def n_check_material_gloss_property(cls, n_mat_prop):
        nose.tools.assert_equal(n_mat_prop.glossiness, 25) # n_gloss = 4/b_gloss
