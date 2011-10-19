"""Exports and imports a simple cube, testing for various features
along the way.
"""

import bpy
import nose.tools

import io_scene_nif.export_nif
from test import Test

class TestCubeExport(Test):
    def setup(self):
        # create a cube
        bpy.ops.mesh.primitive_cube_add()
        self.obj = bpy.data.objects["Cube"]
        self.mesh = self.obj.data

    def test_export(self):
        bpy.ops.export_scene.nif(
            filepath="test/export/cube.nif",
            log_level='DEBUG',
            )

class TestCubeImport(Test):
    def test_import(self):
        bpy.ops.import_scene.nif(
            filepath="test/import/cube.nif",
            log_level='DEBUG',
            )

class TestNonUniformlyScaledCube(Test):
    def setup(self):
        # create a non-uniformly scaled cube
        bpy.ops.mesh.primitive_cube_add()
        self.obj = bpy.data.objects["Cube"]
        self.mesh = self.obj.data
        self.obj.scale = (1, 2, 3)

    @nose.tools.raises(Exception)
    def test_export(self):
        bpy.ops.export_scene.nif(
            filepath="test/export/non_uniformly_scaled_cube.nif",
            log_level='DEBUG',
            )
