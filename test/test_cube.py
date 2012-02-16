"""Exports and imports mesh data"""

import bpy
import nose.tools

from test import SingleNif
from test import Base
from pyffi.formats.nif import NifFormat

class TestBaseCube(SingleNif):
    n_name = "cube/base_cube"
    b_name = "Cube"

    def b_create_object(self):
        # note: primitive_cube_add creates object named "Cube"
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects["Cube"]
        # primitive_cube_add creates a double sided mesh; fix this
        b_obj.data.show_double_sided = False
        return b_obj

    def b_check_object(self, b_obj):
        b_mesh = b_obj.data
        nose.tools.assert_equal(len(b_mesh.vertices), 8)
        num_triangles = len(
            [face for face in b_mesh.faces if len(face.vertices) == 3])
        num_triangles += 2 * len(
            [face for face in b_mesh.faces if len(face.vertices) == 4])
        nose.tools.assert_equal(num_triangles, 12)

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_is_instance(n_geom, NifFormat.NiTriShape)
        nose.tools.assert_equal(n_geom.num_properties, 0)
        nose.tools.assert_equal(n_geom.data.num_vertices, 8)
        nose.tools.assert_equal(n_geom.data.num_triangles, 12)
        
    '''
        TODO: Additional checks needed.
        TriData
            Flags: blender exports| Continue, Maya| Triangles, 
                    Pyffi| test.nif Bound - probably incorrect.
            Consistancy:
            radius:
    '''
class TestNonUniformlyScaledCube(Base):
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
