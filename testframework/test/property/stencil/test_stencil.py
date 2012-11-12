"""Export and import meshes with stencil properties."""

import bpy
import nose.tools
import os

import io_scene_nif.nif_export
from pyffi.formats.nif import NifFormat
from test.geometry.trishape.test_geometry import TestBaseGeometry

class TestStencilProperty(TestBaseGeometry):
    n_name = "property/stencil/stencil"

    def b_create_objects(self):
        TestBaseGeometry.b_create_objects(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_create_stensil_property(b_obj)

    def b_create_stensil_property(self, b_obj):
        b_obj.data.show_double_sided = True

        # bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)

    def b_check_data(self):
        TestBaseGeometry.b_check_data(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_check_stencil_property(b_obj)

    def b_check_stencil_property(self, b_obj):
        nose.tools.assert_equal(b_obj.data.show_double_sided, True)

    def n_check_data(self, n_data):
        TestBaseGeometry.n_check_data(self, n_data)
        self.n_check_block(n_data)

    def n_check_block(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.num_properties, 1)
        self.n_check_stencil_property(n_geom.properties[0])

    def n_check_stencil_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiStencilProperty)

        # TODO - Expand test

