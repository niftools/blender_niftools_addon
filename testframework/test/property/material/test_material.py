"""Export and import material."""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import gen_geometry
from test.property.material import gen_material

class TestMaterialProperty(SingleNif):
    """Test material property"""
    
    n_name = 'property/material/base_material'
    b_name = 'Cube'

    def b_create_objects(self):
        b_obj = gen_geometry.b_create_base_geometry(self.b_name)
        b_obj = self.b_create_material_block(b_obj)
        self.b_create_set_material_property(b_obj.data.materials[0])

    @classmethod
    def b_create_material_block(cls, b_obj):
        b_mat = bpy.data.materials.new(name='Material')
        b_obj.data.materials.append(b_mat)
        bpy.ops.object.shade_smooth()
        return b_obj
    
    @classmethod
    def b_create_set_material_property(cls, b_mat):
        b_mat.diffuse_color = (1.0, 1.0, 1.0) # default - (0.8, 0.8, 0.8)
        b_mat.diffuse_intensity = 1.0 # default - 0.8
        b_mat.specular_intensity = 0.0 # disable NiSpecularProperty
        return b_mat

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        gen_geometry.b_check_geom_obj(b_obj)
        
        b_mat =self.b_check_material_block(b_obj)
        self.b_check_material_property(b_mat)

    @classmethod
    def b_check_material_block(cls, b_obj):
        '''Check that we have a material'''
        
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        nose.tools.assert_equal(len(b_mesh.materials), 1)
        
        return b_mat

    @classmethod
    def b_check_material_property(cls, b_mat):
        '''Check material has the correct properties'''
        
        nose.tools.assert_equal(b_mat.ambient, 1.0)
        nose.tools.assert_equal(b_mat.diffuse_color[0], 1.0)
        nose.tools.assert_equal(b_mat.diffuse_color[1], 1.0)
        nose.tools.assert_equal(b_mat.diffuse_color[2], 1.0)
        nose.tools.assert_equal(b_mat.specular_intensity, 0.0)

    
    def n_create_data(self):
        gen_data.n_create_data(self.n_data)
        gen_geometry.n_create_blocks(self.n_data)
        
        n_trishape = self.n_data.roots[0].children[0]
        gen_material.n_attach_material_prop(n_trishape)
        return self.n_data

    def n_check_data(self, n_data):
        n_nitrishape = n_data.roots[0].children[0]
        gen_geometry.n_check_trishape(n_nitrishape)
        
        nose.tools.assert_equal(n_nitrishape.num_properties, 1) 
        n_mat_prop = n_nitrishape.properties[0]    
        self.n_check_material_block(n_mat_prop)
        self.n_check_material_property(n_mat_prop)

    @classmethod
    def n_check_material_block(cls, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)

    def n_check_material_property(cls, n_mat_prop):
        '''Checks default values'''
        
        nose.tools.assert_equal((n_mat_prop.ambient_color.r,
                                 n_mat_prop.ambient_color.g,
                                 n_mat_prop.ambient_color.b), 
                                (1.0, 1.0, 1.0))

        nose.tools.assert_equal((n_mat_prop.diffuse_color.r,
                                 n_mat_prop.diffuse_color.g,
                                 n_mat_prop.diffuse_color.b), 
                                (1.0, 1.0, 1.0))
        
        nose.tools.assert_equal((n_mat_prop.specular_color.r,
                                 n_mat_prop.specular_color.g,
                                 n_mat_prop.specular_color.b), 
                                (0.0, 0.0, 0.0))
        
        nose.tools.assert_equal((n_mat_prop.emissive_color.r,
                                 n_mat_prop.emissive_color.g,
                                 n_mat_prop.emissive_color.b), 
                                (0.0, 0.0, 0.0))
        
        nose.tools.assert_equal(n_mat_prop.glossiness, 12.5)
        nose.tools.assert_equal(n_mat_prop.alpha, 1.0)
    
        

'''
class TestAmbientMaterial(TestMaterialProperty):
    n_name = "property/material/base_ambient"

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
    n_name = "property/material/base_diffuse"

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
