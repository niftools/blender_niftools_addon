"""Export and import textured meshes."""
"""
    TODO - Find if there are nifs which non-default ambient, diffuse;
        create nitools.prop.color, alter tests as needed.
    TODO_3.0 - Create per material values: ambient, emissive.
    
"""

import bpy
import nose.tools
import os

import io_scene_nif.export_nif
from pyffi.formats.nif import NifFormat
from test.test_geom import TestBaseUV

class TestBaseMaterial(TestBaseUV):
    n_name = "property/material/base_material"

    def b_create_object(self):
        b_obj = TestBaseUV.b_create_object(self)
        b_mat = bpy.data.materials.new(name='Material')
        b_mat.specular_intensity = 0 # disable NiSpecularProperty
        b_obj.data.materials.append(b_mat)
        
        b_mat.ambient = 1.0
        b_mat.diffuse_color = (1.0,1.0,1.0)
        b_mat.diffuse_intensity = 1.0
        
        return b_obj
        
    def b_check_object(self, b_obj):
        b_mesh = b_obj.data
        nose.tools.assert_equal(len(b_mesh.materials), 1)
        b_mat = b_mesh.materials[0]
        nose.tools.assert_equal(b_mat.ambient, 1.0)
        
    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]    
        nose.tools.assert_equal(n_geom.num_properties, 1)
        self.n_check_material_property(n_geom.properties[0])
        
    '''
        self.n_check_flags(n_data.header())

    def n_check_flags(self, n_header):
        pass
         TODO 
        if(self.n_header.version == 'MORROWIND'):
            nose.tools.assert_equal(n_geom.properties[0].flags == 1)
    '''

    def n_check_material_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)
        #TODO - Refer to header - can be ignored for now, no use found.                  
        nose.tools.assert_equal((n_mat_prop.ambient_color.r,
                                 n_mat_prop.ambient_color.g,
                                 n_mat_prop.ambient_color.b), (1.0,1.0,1.0))
        
        nose.tools.assert_equal((n_mat_prop.diffuse_color.r,
                                 n_mat_prop.diffuse_color.g,
                                 n_mat_prop.diffuse_color.b), (1.0,1.0,1.0))


class TestEmissiveMaterial(TestBaseMaterial):
    n_name = "property/material/base_emissive"
    
    def b_create_object(self):
        b_obj = TestBaseMaterial.b_create_object(self)
        b_mat = b_obj.data.materials[0]
        #TODO: Skyrim refactor
        #b_mat.niftools.emissive_color = (1.0,1.0,1.0)
        #map b_mat.material.emit update_func() -> b_mat.niftools.emissive_factor 
        #b_mat.niftools.emissive_factor = 1.0 
        b_mat.emit = 1.0
        
        return b_obj
        
    def b_check_object(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        nose.tools.assert_equal(b_mat.emit, 1.0)
        #nose.tools.assert-equal(b_mat.niftools.emissive_factor, b_mat.emit)
        
    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        self.n_check_material_emissive_property(n_geom.properties[0])

    def n_check_material_emissive_property(self, n_mat_prop):
        #TODO - Refer to header
        nose.tools.assert_equal((n_mat_prop.emissive_color.r,
                                 n_mat_prop.emissive_color.g,
                                 n_mat_prop.emissive_color.b), (1.0,1.0,1.0))
        
'''
    TODO - alpha, stencil, etc.
'''

'''
class TestAmbientMaterial(TestBaseMaterial):
    n_name = "property/material/base_material"

    def b_create_object(self):
        b_obj = TestBaseUV.b_create_object(self)
        b_mat = b_obj.data.materials[0]
                
        #diffuse settings
        b_mat.niftools.ambient_color = (0.0,1.0,0.0)#TODO_3.0 - update func-> World ambient
        return b_obj
        
    def b_check_object(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        nose.tools.assert_equal(b_mat.niftools.ambient_color, (0.0,1.0,0.0))
        
    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        self.n_check_material_property(n_geom.properties[0])

    def n_check_material_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)
        nose.tools.assert_equal(n_mat_prop.ambient_color, (0.0,1.0,0.0))

class TestDiffuseMaterial(TestBaseMaterial):
    n_name = "property/material/base_material"

    def b_create_object(self):
        b_obj = TestBaseUV.b_create_object(self)
        b_mat = b_obj.data.materials[0]
        
        #diffuse settings
        b_mat.niftools.diffuse_color = (0.0,1.0,0.0)#TODO_3.0 - update func-> World ambient 
        return b_obj
        
    def b_check_object(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        nose.tools.assert_equal(b_mat.niftools.diffuse_color, (0.0,1.0,0.0))
        
    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        self.n_check_material_property(n_geom.properties[0])

    def n_check_material_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)
        nose.tools.assert_equal(n_mat_prop.diffuse_color, (0.0,1.0,0.0))
'''
    
