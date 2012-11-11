"""Export and import material meshes."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.geometry.trishape.gen_geometry import TriShapeGeometry
from test.geometry.trishape.test_geometry import TestBaseGeometry
from test.property.material.gen_material import Material

class TestMaterialProperty(SingleNif):
    
    def __init__(self):
        self.n_name = "property/material/base_material"
        
        self.b_name = "Cube"
        
        self.n_data = self.n_create_data()
        """Read code to generate physical Nif"""
        
        SingleNif.__init__(self)

    def b_create_objects(self):
        b_obj = TestBaseGeometry().b_create_base_geometry()
        b_obj.name = self.b_name
        self.b_create_material_block(b_obj)

    def b_create_material_block(self, b_obj):
        b_mat = bpy.data.materials.new(name='Material')
        b_mat.specular_intensity = 0 # disable NiSpecularProperty
        b_obj.data.materials.append(b_mat)
        bpy.ops.object.shade_smooth()
        self.b_create_material_property(b_mat)
        
        return b_obj

    def b_create_material_property(self, b_mat):
        # TODO_3.0 - See above
        b_mat.ambient = 1.0
        b_mat.diffuse_color = (1.0,1.0,1.0)
        b_mat.diffuse_intensity = 1.0

        # bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        TestBaseGeometry().b_check_geom_obj(b_obj)
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

    def n_create_data(self):
        data = TriShapeGeometry().n_create()
        data = Material().n_create(data)
        return data

    def n_check_data(self, n_data):
        TestBaseGeometry().n_check_data(n_data)
        self.n_check_material_block(n_data)
        
    def n_check_material_block(self, n_data):
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
        
'''
class TestAmbientMaterial(TestMaterialProperty):
    n_name = "property/material/base_material"

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
    n_name = "property/material/base_material"

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