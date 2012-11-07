"""Export and import material meshes."""

#    TODO_material - Find any nifs with non-default ambient, diffuse;
#    TODO_3.0 - Create per material values: niftools.ambient, niftools.emissive.

import bpy
import nose.tools
import os

import io_scene_nif.nif_export
from pyffi.formats.nif import NifFormat
from test.geometry.test_geometry import TestBaseGeometry

class TestMaterialProperty(TestBaseGeometry):
    n_name = "property/material/base_material"

    def b_create_objects(self):
        TestBaseGeometry.b_create_objects(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_create_material_block(b_obj)

    def b_create_material_block(self, b_obj):
        b_mat = bpy.data.materials.new(name='Material')
        b_mat.specular_intensity = 0 # disable NiSpecularProperty
        b_obj.data.materials.append(b_mat)
        bpy.ops.object.shade_smooth()
        self.b_create_material_property(b_mat)

    def b_create_material_property(self, b_mat):
        # TODO_3.0 - See above
        b_mat.ambient = 1.0
        b_mat.diffuse_color = (1.0,1.0,1.0)
        b_mat.diffuse_intensity = 1.0

        # bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)

    def b_check_data(self):
        TestBaseGeometry.b_check_data(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_check_material_block(b_obj)

    def b_check_material_block(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        nose.tools.assert_equal(len(b_mesh.materials), 1)
        self.b_check_material_property(b_mat)

    def b_check_material_property(self, b_mat):
        nose.tools.assert_equal(b_mat.ambient, 1.0)
        nose.tools.assert_equal(b_mat.diffuse_color[0], 1.0)
        nose.tools.assert_equal(b_mat.diffuse_color[1], 1.0)
        nose.tools.assert_equal(b_mat.diffuse_color[2], 1.0)

    def n_check_data(self, n_data):
        TestBaseGeometry.n_check_data(self, n_data)
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.num_properties, 1)
        self.n_check_material_property(n_geom.properties[0])

    '''
    TODO_3.0 - per version checking????
        self.n_check_flags(n_data.header())

    def n_check_flags(self, n_header):
        pass
        if(self.n_header.version == 'MORROWIND'):
            nose.tools.assert_equal(n_geom.properties[0].flags == 1)
    '''

    def n_check_material_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)
        # TODO - Refer to header - can be ignored for now, defaults.
        nose.tools.assert_equal((n_mat_prop.ambient_color.r,
                                 n_mat_prop.ambient_color.g,
                                 n_mat_prop.ambient_color.b), (1.0,1.0,1.0))

        nose.tools.assert_equal((n_mat_prop.diffuse_color.r,
                                 n_mat_prop.diffuse_color.g,
                                 n_mat_prop.diffuse_color.b), (1.0,1.0,1.0))
