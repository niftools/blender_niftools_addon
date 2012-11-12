"""Export and import material meshes."""

import bpy
import nose.tools
import os

import io_scene_nif.nif_export
from pyffi.formats.nif import NifFormat
from test.geometry.trishape.test_geometry import TestBaseGeometry
from test.property.material.test_material import TestMaterialProperty


class TestGlossProperty(TestMaterialProperty):
    n_name = "property/material/base_material"

    def b_create_objects(self):
        TestMaterialProperty.b_create_objects(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_create_gloss_property(b_obj)

    def b_create_gloss_property(self, b_obj):
        b_mat = b_obj.data.materials[0]
        b_mat.specular_hardness = 100

    def b_check_data(self):
        TestMaterialProperty.b_check_data(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_check_gloss_block(b_obj)

    def b_check_gloss_block(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        self.b_check_gloss_property(b_mat)

    def b_check_gloss_property(self, b_mat):
        nose.tools.assert_equal(b_mat.specular_hardness, 100)

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        self.n_check_material_gloss_property(n_geom.properties[0])
        self.n_check_material_property(n_geom.properties[0])

    def n_check_material_gloss_property(self, n_mat_prop):
        nose.tools.assert_equal(n_mat_prop.glossiness, 25) # n_gloss = 4/b_gloss
