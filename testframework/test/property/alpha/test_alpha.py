"""Export and import material meshes."""

import bpy
import nose.tools
import os

import io_scene_nif.nif_export
from pyffi.formats.nif import NifFormat
from test.geometry.trishape.test_geometry import TestBaseGeometry
from test.property.material.test_material import TestMaterialProperty

class TestAlphaProperty(TestMaterialProperty):
    n_name = "property/alpha/base_alpha"

    def b_create_objects(self):
        TestMaterialProperty.b_create_objects(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_create_alpha_property(b_obj)

    def b_create_alpha_property(self, b_obj):
        b_mat = b_obj.data.materials[0]
        b_mat.use_transparency = True
        b_mat.alpha = 0.5
        b_mat.transparency_method = 'Z_TRANSPARENCY'

        # bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)

    def b_check_data(self):
        TestMaterialProperty.b_check_data(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_check_alpha_block(b_obj)

    def b_check_alpha_block(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        self.b_check_alpha_property(b_mat)

    def b_check_alpha_property(self, b_mat):
        nose.tools.assert_equal(b_mat.use_transparency, True)
        nose.tools.assert_equal(b_mat.alpha, 0.5)
        nose.tools.assert_equal(b_mat.transparency_method, 'Z_TRANSPARENCY')

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.num_properties, 2)
        self.n_check_alpha_property(n_geom.properties[0])
        self.n_check_material_property(n_geom.properties[1])

    def n_check_alpha_property(self, n_alpha_prop):
        nose.tools.assert_is_instance(n_alpha_prop, NifFormat.NiAlphaProperty)
        # TODO Check Prop Settings
