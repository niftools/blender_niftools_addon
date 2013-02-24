"""Exports and imports mesh data"""

import bpy
import nose.tools
import math
import mathutils

from pyffi.formats.nif import NifFormat

from test import Base
from test import SingleNif
from test.data import gen_data 
from test.geometry.trishape import b_gen_geometry
from test.geometry.trishape import n_gen_geometry

class TestBaseGeometry(SingleNif):
    """Test base geometry, single blender object."""

    n_name = 'geometry/trishape/test_trishape' # (documented in base class)
    b_name = 'Cube'

    def b_create_objects(self):
        # (documented in base class)
        b_obj = b_gen_geometry.b_create_cube(self.b_name)
        
        # transform it into something less trivial
        b_gen_geometry.b_scale_object()
        b_gen_geometry.b_scale_single_face(b_obj)
        b_obj.matrix_local = b_gen_geometry.b_get_transform_matrix()
    
    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_geometry.b_check_geom_obj(b_obj)

    def n_create_data(self):
        gen_data.n_create_header(self.n_data)
        n_gen_geometry.n_create_blocks(self.n_data)
        return self.n_data

    def n_check_data(self):
        n_trishape = self.n_data.roots[0].children[0]
        n_gen_geometry.n_check_trishape(n_trishape)

class TestNonUniformlyScaled(Base):
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

