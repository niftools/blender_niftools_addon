"""Export and import textured meshes."""

import bpy
import nose.tools
import os

import io_scene_nif.export_nif
from pyffi.formats.nif import NifFormat
from test.test_cube import TestBaseCube

class TestBaseMaterial(TestBaseCube):
    n_name = "material/base_material"

    def b_create_object(self):
        b_obj = TestBaseCube.b_create_object(self)
        b_mat = bpy.data.materials.new(name='Material')
        b_mat.specular_intensity = 0 # disable NiSpecularProperty
        b_obj.data.materials.append(b_mat)
        return b_obj
        
    def b_check_object(self, b_obj):
        b_mesh = b_obj.data
        nose.tools.assert_equal(len(b_mesh.materials), 1)
        b_mat = b_mesh.materials[0]

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]    
        nose.tools.assert_equal(n_geom.num_properties, 1)
        self.n_check_material_property(n_geom.properties[0])

    def n_check_material_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)


    '''
        TODO - alpha, stencil, etc.
    '''