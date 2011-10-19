"""Export and import textured meshes."""

import bpy
import nose.tools

import io_scene_nif.export_nif
from test import Test

class TestBaseUVTextureImport(Test):
    def test_import(self):
        bpy.ops.import_scene.nif(
            filepath="test/import/base_uv_texture.nif",
            log_level='DEBUG',
            )

class TestBaseUVTextureExport(Test):
    def setup(self):
        # create a cube
        bpy.ops.mesh.primitive_cube_add()
        self.obj = bpy.data.objects["Cube"]
        self.mesh = self.obj.data
        # TODO add a texture to it

    def test_export(self):
        bpy.ops.export_scene.nif(
            filepath="test/export/base_uv_texture.nif",
            log_level='DEBUG',
            )
