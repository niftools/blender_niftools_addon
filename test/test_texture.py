"""Export and import textured meshes."""

    #TODO - Set Material Render to GLSL
    #TODO - alpha, dark, detail, specular.
    #TODO_3.0 - Unify pathing checks per game.

'''    
    Notes
    Blender auto-gen 18 slots, need to use create slots?
    Compare exporter for auto-gen data & nif format for additional checks
'''

import bpy
import nose.tools
import os.path

import io_scene_nif.nif_export
from pyffi.formats.nif import NifFormat
from test.test_geometry import TestBaseUV
from test.test_property import TestMaterialProperty

#NiTexturingProperty
class TestBaseTexture(TestBaseUV, TestMaterialProperty):
    # (documented in base class)
    n_name = "textures/base_texture"

    diffuse_texture_path = os.path.join(
        'test', 'nif', 'textures', 'base_texture.dds')

    def b_create_objects(self):
        TestBaseUV.b_create_objects(self) # create uv-wrapped obj
        b_obj = bpy.data.objects[self.b_name]
        TestMaterialProperty.b_create_material_block(self, b_obj)
        b_mat = b_obj.data.materials[0]
        self.b_create_diffuse_texslot(b_mat)
        
    def b_create_diffuse_texslot(self, b_mat):
        b_mat_texslot = b_mat.texture_slots.create(0) # create material texture slot                        
        b_mat_texslot.texture = bpy.data.textures.new(name='DiffuseTexture', type='IMAGE') # create texture holder
        b_mat_texslot.texture.image = bpy.data.images.load(self.diffuse_texture_path)
        b_mat_texslot.use = True
        b_mat_texslot.texture_coords = 'UV'
        b_mat_texslot.uv_layer = 'UVMap'
        b_mat_texslot.use_map_color_diffuse = True

        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
    
    def b_check_data(self):
        # TODO fails b_mesh.vertices is not 8??
        #TestBaseUV.b_check_data(self)
        #TestMaterialProperty.b_check_data(self) 
        b_obj = bpy.data.objects[self.b_name]
        self.b_check_texture_block(b_obj)
        
    def b_check_texture_block(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        
        nose.tools.assert_equal(b_mat.texture_slots[0] != None, True) # check slot exists
        b_mat_texslot = b_mat.texture_slots[0]
        nose.tools.assert_equal(b_mat_texslot.use, True) # check slot enabled
        self.b_check_texture_property(b_mat_texslot)
    
    def b_check_texture_property(self, b_mat_texslot):
        nose.tools.assert_is_instance(b_mat_texslot.texture, bpy.types.ImageTexture)
        #nose.tools.assert_equal(b_mat_texslot.texture.image.filepath, self.diffuse_texture_path)
        nose.tools.assert_equal(b_mat_texslot.texture_coords, 'UV')
        
        nose.tools.assert_equal(b_mat_texslot.use_map_color_diffuse, True)
        
    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.num_properties, 2)
        self.n_check_texturing_property(n_geom.properties[0])
        self.n_check_material_property(n_geom.properties[1])

    def n_check_texturing_property(self, n_tex_prop):
        nose.tools.assert_is_instance(n_tex_prop, NifFormat.NiTexturingProperty)
        nose.tools.assert_equal(n_tex_prop.apply_mode, 2)
        nose.tools.assert_equal(n_tex_prop.has_base_texture, True)
        self.n_check_base_texture(n_tex_prop.base_texture) 

    def n_check_base_texture(self, n_texture):
        nose.tools.assert_equal(n_texture.clamp_mode, 3)
        nose.tools.assert_equal(n_texture.filter_mode, 2)
        nose.tools.assert_equal(n_texture.uv_set, 0)
        nose.tools.assert_equal(n_texture.has_texture_transform, False)
        self.n_check_base_source_texture(n_texture.source)

    def n_check_base_source_texture(self, n_source):
        nose.tools.assert_is_instance(n_source, NifFormat.NiSourceTexture)
        nose.tools.assert_equal(n_source.use_external, 1)
        #nose.tools.assert_equal(n_source.file_name, self.diffuse_texture_path)


class TestBumpTexture(TestBaseTexture):
    texture_filepath = 'test' + os.sep + 'nif'+ os.sep + 'textures' + os.sep + 'base_bump.dds'

    def b_create_objects(self):
        #create material texture slot
        TestBaseTexture.b_create_objects(self)
        b_obj = bpy.data.objects[self.b_name]
        b_mat = b_obj.data.materials[0]         
        b_mat_texslot = b_mat.texture_slots.create(1)

        #user manually selects Image Type then loads image
        b_mat_texslot.texture = bpy.data.textures.new(name='BumpTexture', type='IMAGE')
        b_mat_texslot.texture.image = bpy.data.images.load(self.texture_filepath)
        b_mat_texslot.use = True
        
        #Influence mapping
        b_mat_texslot.use_map_color_diffuse = False #auto-set on creation
        b_mat_texslot.texture.use_normal_map = False #causes artifacts otherwise.

        #Mapping
        b_mat_texslot.texture_coords = 'UV'
        b_mat_texslot.uv_layer = 'UVMap'
        
        #Influence
        b_mat_texslot.use_map_normal = True

        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        return b_obj
        
    def b_check_data(self):
        # TODO fails b_mesh.vertices is not 8??
        #TestBaseTexture.b_check_data(self)
        b_obj = bpy.data.objects[self.b_name]
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        b_mat_texslot = b_mat.texture_slots[1]
        
        nose.tools.assert_is_instance(b_mat_texslot.texture, bpy.types.ImageTexture)
        #nose.tools.assert_equal(b_mat_texslot.texture.image.filepath, self.texture_filepath)
        nose.tools.assert_equal(b_mat_texslot.use, True)
        
        nose.tools.assert_equal(b_mat_texslot.texture.use_normal_map, False)
        nose.tools.assert_equal(b_mat_texslot.texture_coords, 'UV')
        nose.tools.assert_equal(b_mat_texslot.use_map_color_diffuse, False)
        nose.tools.assert_equal(b_mat_texslot.use_map_normal, True)

    def n_check_data(self, n_data):
        TestBaseTexture.n_check_data(self, n_data)
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.num_properties, 2)
        self.n_check_texturing_property(n_geom.properties[0])
        self.n_check_material_property(n_geom.properties[1])

    def n_check_texturing_property(self, n_tex_prop):
        nose.tools.assert_is_instance(n_tex_prop, NifFormat.NiTexturingProperty)
        nose.tools.assert_equal(n_tex_prop.has_bump_map_texture, True)
        nose.tools.assert_equal(n_tex_prop.bump_map_luma_scale, 1.0)
        nose.tools.assert_equal(n_tex_prop.bump_map_luma_offset, 0.0)
        nose.tools.assert_equal(n_tex_prop.bump_map_matrix.m_11, 1.0)
        nose.tools.assert_equal(n_tex_prop.bump_map_matrix.m_12, 0.0)
        nose.tools.assert_equal(n_tex_prop.bump_map_matrix.m_21, 0.0)
        nose.tools.assert_equal(n_tex_prop.bump_map_matrix.m_22, 1.0)
        self.n_check_bump_texture(n_tex_prop.bump_map_texture)

    def n_check_bump_texture(self, n_texture):
        nose.tools.assert_equal(n_texture.clamp_mode, 3)
        nose.tools.assert_equal(n_texture.filter_mode, 2)
        nose.tools.assert_equal(n_texture.uv_set, 0)
        nose.tools.assert_equal(n_texture.has_texture_transform, False)
        self.n_check_base_source_texture(n_texture.source)
        
    def n_check_base_source_texture(self, n_source):
        nose.tools.assert_is_instance(n_source, NifFormat.NiSourceTexture)
        nose.tools.assert_equal(n_source.use_external, 1)
        #nose.tools.assert_equal(n_source.file_name, self.texture_filepath)

'''
Normal map, technically special case....
Handling if user supplies normal map instead of bump & vice-versa

    Extra_shader_data -> NormalMapIndex (Civ VI, Sid Miener)
    BSShaderPPLightingProperty (FO3 & NV)
    BSLightingShaderProperty(Skyrim)
    
class TestNormalTexture(TestBaseTexture):
    n_name = "textures/normal_texture"
    texture_filepath = 'test' + os.sep + 'nif'+ os.sep + 'textures' + os.sep + 'base_normal.dds'

    def b_create_objects(self):
        b_obj = TestBaseTexture.b_create_objects(self)
        b_mat = b_obj.data.materials[0]
        
        #create texture slot 
        b_mat_texslot = b_mat.texture_slots.create(1)

        #user manually selects Image Type then loads image
        b_mat_texslot.texture = bpy.data.textures.new(name='NormalTexture', type='IMAGE')
        b_mat_texslot.texture.image = bpy.data.images.load(self.texture_filepath)
        b_mat_texslot.use = True

        #Inflence mapping
        b_mat_texslot.texture.use_normal_map = True
        
        #Mapping
        b_mat_texslot.texture_coords = 'UV'
        b_mat_texslot.uv_layer = 'UVMap'
        
        #Influence
        b_mat_texslot.use_map_normal = True
        
        
    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_mesh = b_obj.data
        nose.tools.assert_equal(len(b_mesh.materials), 1)
        b_mat = b_mesh.materials[0]
        b_mat_texslot = b_mat.texture_slots[0]
        nose.tools.assert_equal(b_mat_texslot.use, True)
        nose.tools.assert_is_instance(b_mat_texslot.texture, bpy.types.ImageTexture)
        nose.tools.assert_equal(b_mat_texslot.texture.image.filepath, self.texture_filepath)
        nose.tools.assert_equal(b_mat_texslot.texture_coords, 'UV')
        nose.tools.assert_equal(b_mat_texslot.use_map_normal, True)

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        self.n_check_texturing_property(n_geom.properties[0])

    def n_check_texturing_property(self, n_tex_prop):
        nose.tools.assert_is_instance(n_tex_prop, NifFormat.NiTexturingProperty)
        nose.tools.assert_equal(n_tex_prop.has_, True)
        self.n_check_base_texture(n_tex_prop.base_texture) 

'''
class TestGlowTexture(TestBaseTexture):
    texture_filepath = 'test' + os.sep + 'nif'+ os.sep + 'textures' + os.sep + 'base_glow.dds'

    def b_create_objects(self):
        #create material texture slot
        TestBaseTexture.b_create_objects(self)
        b_obj = bpy.data.objects[self.b_name]
        b_mat = b_obj.data.materials[0]
        b_mat_texslot = b_mat.texture_slots.create(2)

        #user manually selects Image Type then loads image
        b_mat_texslot.texture = bpy.data.textures.new(name='GlowTexture', type='IMAGE')
        b_mat_texslot.texture.image = bpy.data.images.load(self.texture_filepath)
        b_mat_texslot.use = True
        
        #Influence mapping
        b_mat_texslot.use_map_color_diffuse = False
        b_mat_texslot.texture.use_alpha = False #If no alpha channel or white causes display error
        
        #Mapping
        b_mat_texslot.texture_coords = 'UV'
        b_mat_texslot.uv_layer = 'UVMap'
        
        #Influence
        b_mat_texslot.use_map_emit = True

        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        return b_obj
        
    def b_check_data(self):
        # TODO fails b_mesh.vertices is not 8??
        #TestBaseTexture.b_check_data(self)
        b_obj = bpy.data.objects[self.b_name]
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        b_mat_texslot = b_mat.texture_slots[2]
        
        nose.tools.assert_is_instance(b_mat_texslot.texture, bpy.types.ImageTexture)
        #nose.tools.assert_equal(b_mat_texslot.texture.image.filepath, self.texture_filepath)
        nose.tools.assert_equal(b_mat_texslot.use, True)
        nose.tools.assert_equal(b_mat_texslot.texture.use_alpha, False)
        nose.tools.assert_equal(b_mat_texslot.texture_coords, 'UV')
        nose.tools.assert_equal(b_mat_texslot.use_map_color_diffuse, False)
        nose.tools.assert_equal(b_mat_texslot.use_map_emit, True)
        
    def n_check_data(self, n_data):
        TestBaseTexture.n_check_data(self, n_data)
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.num_properties, 2)
        self.n_check_texturing_property(n_geom.properties[0])
        self.n_check_material_property(n_geom.properties[1])

    def n_check_texturing_property(self, n_tex_prop):
        nose.tools.assert_is_instance(n_tex_prop, NifFormat.NiTexturingProperty)
        nose.tools.assert_equal(n_tex_prop.has_glow_texture, True)
        self.n_check_glow_texture(n_tex_prop.glow_texture) 

    def n_check_glow_texture(self, n_texture):
        nose.tools.assert_equal(n_texture.clamp_mode, 3)
        nose.tools.assert_equal(n_texture.filter_mode, 2)
        nose.tools.assert_equal(n_texture.uv_set, 0)
        nose.tools.assert_equal(n_texture.has_texture_transform, False)
        self.n_check_base_source_texture(n_texture.source)
        
    def n_check_base_source_texture(self, n_source):
        nose.tools.assert_is_instance(n_source, NifFormat.NiSourceTexture)
        nose.tools.assert_equal(n_source.use_external, 1)
        #nose.tools.assert_equal(n_source.file_name, self.texture_filepath)     
