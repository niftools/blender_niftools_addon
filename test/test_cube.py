"""Exports and imports a simple cube, testing for various features
along the way.
"""

import bpy
import nose.tools
import test

from pyffi.formats.nif import NifFormat

class TestCube(test.SingleNif):
    name = "cube"

    def b_create(self):
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects["Cube"]

    def b_check(self):
        b_obj = bpy.data.objects["Cube"]
        b_mesh = b_obj.data
        nose.tools.assert_equal(len(b_mesh.vertices), 8)
        num_triangles = len(
            [face for face in b_mesh.faces if len(face.vertices) == 3])
        num_triangles += 2 * len(
            [face for face in b_mesh.faces if len(face.vertices) == 4])
        nose.tools.assert_equal(num_triangles, 12)

    def b_select(self):
        bpy.data.objects["Cube"].select = True

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_is_instance(n_geom, NifFormat.NiTriShape)
        nose.tools.assert_equal(n_geom.data.num_vertices, 8)
        nose.tools.assert_equal(n_geom.data.num_triangles, 12)

class TestNonUniformlyScaledCube(test.Base):
    def setup(self):
        # create a non-uniformly scaled cube
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects["Cube"]
        b_obj.scale = (1, 2, 3)

    @nose.tools.raises(Exception)
    def test_export(self):
        bpy.ops.export_scene.nif(
            filepath="test/export/non_uniformly_scaled_cube.nif",
            log_level='DEBUG',
            )
