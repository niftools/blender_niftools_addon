"""Import and Export UV Data"""

import bpy
import nose.tools
import math
import mathutils

from test.geometry.trishape.test_geometry import TestBaseGeometry
from pyffi.formats.nif import NifFormat

class TestBaseUV(TestBaseGeometry):
    n_name = "geometry/uvdata/base_uv"

    def b_create_objects(self):
        TestBaseGeometry.b_create_objects(self)
        b_obj = bpy.data.objects[self.b_name]
        self.b_create_uv_object(b_obj)

    def b_create_uv_object(self, b_obj):
        # project UV
        bpy.ops.object.mode_set(mode='EDIT', toggle=False) # ensure we are in the mode.
        bpy.ops.uv.cube_project() # named 'UVTex'
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        # bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)
        return b_obj

    def b_check_data(self):
        TestBaseGeometry.b_check_data(self)
        pass
        '''
        b_obj = bpy.data.objects[self.b_name]
        b_mesh = b_obj.data
        nose.tools.assert_equal(len(b_mesh.uv_textures), 1)
        nose.tools.assert_equal()
        '''
        # TODO_3.0 - Separate out the UV writing from requiring a texture.

    def n_check_data(self, n_data):
        TestBaseGeometry.n_check_data(self, n_data)
        pass
        '''
        #TODO_3.0 - See above
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(len(n_geom.data.uv_sets), 1)
        nose.tools.assert_equal(len(n_geom.data.uv_sets[0]), len(n_geom.data.vertices))
        '''
