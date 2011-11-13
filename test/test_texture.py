"""Export and import textured meshes."""

import bpy
import nose.tools

import io_scene_nif.export_nif
import test

class TestBaseUVTextureImport(test.Base):
    def test_import(self):
        bpy.ops.import_scene.nif(
            filepath="test/import/base_uv_texture.nif",
            log_level='DEBUG',
            )

class TestBaseUVTextureExport(test.Base):
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
