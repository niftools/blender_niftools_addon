"""Export and import textured meshes."""

import bpy
import nose.tools
import os

import io_scene_nif.export_nif
from pyffi.formats.nif import NifFormat
from test.test_material import TestMaterial

class TestBaseUVTexture(TestMaterial):
    n_name = "texture/base_uv_texture"

    def b_create_object(self):
        b_obj = TestCube.b_create_object(self)
        b_mtex = b_mat.texture_slots.create(0)
        b_mtex.texture_coords = 'UV'
        b_mtex.use_map_color_diffuse = True
        b_mtex.texture = bpy.data.textures.new(name='Tex', type='IMAGE')
        b_mtex.texture.image = bpy.data.images.new('textures' + os.sep + 'image.dds', 1, 1)
        bpy.ops.object.editmode_toggle()
        bpy.ops.uv.cube_project() # named 'UVTex'
        bpy.ops.object.editmode_toggle()
        b_mtex.uv_layer = 'UVTex'
        return b_obj

    def b_check_object(self, b_obj):
        b_mesh = b_obj.data
        nose.tools.assert_equal(len(b_mesh.materials), 1)
        b_mat = b_mesh.materials[0]
        b_mtex = b_mat.texture_slots[0]
        nose.tools.assert_equal(b_mtex.use, True)
        nose.tools.assert_equal(b_mtex.texture_coords, 'UV')
        nose.tools.assert_equal(b_mtex.use_map_color_diffuse, True)
        nose.tools.assert_is_instance(b_mtex.texture, bpy.types.ImageTexture)
        nose.tools.assert_equal(
            b_mtex.texture.image.filepath, 'textures' + os.sep + 'image.dds')

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(len(n_geom.data.uv_sets), 1)
        nose.tools.assert_equal(
            len(n_geom.data.uv_sets[0]), len(n_geom.data.vertices))
        nose.tools.assert_equal(n_geom.num_properties, 2)
        self.n_check_texturing_property(n_geom.properties[0])

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
        nose.tools.assert_equal(n_source.file_name, b"textures\\image.dds")


'''
    TODO - alpha, glow, normal, dark, detail, specular,  