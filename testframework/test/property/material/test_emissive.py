"""Export and import material meshes."""

import bpy
import nose.tools
import os

import io_scene_nif.nif_export
from pyffi.formats.nif import NifFormat
from test.geometry.trishape.test_geometry import TestBaseGeometry
from test.property.material.test_material import TestMaterialProperty

class TestEmissiveMaterial(TestMaterialProperty):
    n_name = "property/material/base_material"

    def b_create_objects(self):
        TestMaterialProperty.b_create_objects(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_create_emmisive_property(b_obj)

    def b_create_emmisive_property(self, b_obj):
        b_mat = b_obj.data.materials[0]
        b_mat.niftools.emissive_color = (0.5,0.0,0.0)
        b_mat.emit = 1.0

        # bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)

    def b_check_data(self):
        TestMaterialProperty.b_check_data(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_check_emmisive_block(b_obj)

    def b_check_emmisive_block(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        self.b_check_emmision_property(b_mat)

    def b_check_emmision_property(self, b_mat):
        nose.tools.assert_equal(b_mat.emit, 1.0)
        nose.tools.assert_equal((b_mat.niftools.emissive_color.r,
                                 b_mat.niftools.emissive_color.g,
                                 b_mat.niftools.emissive_color.b),
                                (0.5,0.0,0.0))

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        self.n_check_material_emissive_property(n_geom.properties[0])
        self.n_check_material_property(n_geom.properties[0])

    def n_check_material_emissive_property(self, n_mat_prop):
        # TODO - Refer to header
        nose.tools.assert_equal((n_mat_prop.emissive_color.r,
                                 n_mat_prop.emissive_color.g,
                                 n_mat_prop.emissive_color.b),
                                (0.5,0.0,0.0))