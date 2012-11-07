"""Export and import material meshes."""

import bpy
import nose.tools
import os

import io_scene_nif.nif_export
from pyffi.formats.nif import NifFormat
from test.geometry.trishape.test_geometry import TestBaseGeometry
from test.property.material.test_material import TestMaterialProperty

class TestWireFrameProperty(TestMaterialProperty):
    n_name = "property/wireframe/base_wire"

    def b_create_objects(self):
        TestMaterialProperty.b_create_objects(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_create_wireframe_property(b_obj)

    def b_create_wireframe_property(self, b_obj):
        b_mat = b_obj.data.materials[0]
        b_mat.type = 'WIRE';

        # bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)

    def b_check_data(self):
        TestMaterialProperty.b_check_data(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_check_wire_block(b_obj)

    def b_check_wire_block(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        self.b_check_wire_property(b_mat)

    def b_check_wire_property(self, b_mat):
        nose.tools.assert_equal(b_mat.type, 'WIRE')

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.num_properties, 2)
        self.n_check_wire_property(n_geom.properties[0])
        self.n_check_material_property(n_geom.properties[1])

    def n_check_wire_property(self, n_wire_prop):
        nose.tools.assert_is_instance(n_wire_prop, NifFormat.NiWireframeProperty)
        nose.tools.assert_equal(n_wire_prop.flags, 0x1)

