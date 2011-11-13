"""Export and import textured meshes."""

import bpy
import nose.tools
import io_scene_nif.export_nif
from pyffi.formats.nif import NifFormat
from test.test_cube import TestCube

class TestBaseUVTexture(TestCube):
    n_name = "base_uv_texture"

    def b_create_object(self):
        b_obj = TestCube.b_create_object()
        # TODO add a texture to it
        return b_obj

    def b_check_object(self, b_obj):
        # TODO check for presence of a texture
        pass

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.num_properties, 1)
        nose.tools.assert_equal(len(n_geom.data.uv_sets), 1)
        nose.tools.assert_equal(len(n_geom.data.uv_sets[0]), 8) # 8 vertices
        with n_geom.properties[0] as n_tex_prop:
            nose.tools.assert_is_instance(
                n_tex_prop, NifFormat.NiTexturingProperty)
            nose.tools.assert_equal(n_tex_prop.apply_mode, 2)
            nose.tools.assert_equal(n_tex_prop.has_base_texture, True)
            with n_tex_prop.base_texture as n_texture:
                with n_texture.source as n_source:
                    nose.tools.assert_is_instance(
                        n_source, NifFormat.NiSourceTexture)
                    nose.tools.assert_equal(n_source.use_external, 1)
                    nose.tools.assert_equal(
                        n_source.file_name, "texture\\image.dds")
                nose.tools.assert_equal(n_texture.clamp_mode, 3)
                nose.tools.assert_equal(n_texture.filter_mode, 2)
                nose.tools.assert_equal(n_texture.uv_set, 0)
                nose.tools.assert_equal(n_texture.has_texture_transform, False)
        with n_geom.properties[1] as n_mat_prop:
            nose.tools.assert_is_instance(
                n_mat_prop, NifFormat.NiMaterialProperty)
