"""Export and import textured meshes."""

import bpy
import nose.tools
import io_scene_nif.export_nif
from pyffi.formats.nif import NifFormat
from test.test_cube import TestCube

class TestBaseUVTexture(TestCube):
    n_name = "base_uv_texture"

    def b_create_object(self):
        b_obj = TestCube.b_create_object(self)
        # TODO add a texture to it
        return b_obj

    def b_check_object(self, b_obj):
        # TODO check for presence of a texture
        pass

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(len(n_geom.data.uv_sets), 1)
        nose.tools.assert_equal(
            len(n_geom.data.uv_sets[0]), len(n_geom.data.vertices))
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
        nose.tools.assert_equal(n_source.file_name, b"textures\\image.dds")

    def n_check_material_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)
