"""Exports and imports a simple cube, testing for various features
along the way.
"""

import sys

import bpy

class TestCubeExport:
    def setup(self):
        # create a cube
        bpy.ops.mesh.primitive_cube_add()
        self.obj = bpy.data.objects["Cube"]
        self.mesh = self.obj.data

    def test_export(self):
        bpy.ops.export_scene.nif(
            filepath="test/tmp/test_cube_export.nif",
            log_level='DEBUG',
            )

    def teardown(self):
        # destroy cube
        bpy.context.scene.objects.unlink(self.obj)
        bpy.data.objects.remove(self.obj)
        bpy.data.meshes.remove(self.mesh)

class TestCubeImport:
    pass
