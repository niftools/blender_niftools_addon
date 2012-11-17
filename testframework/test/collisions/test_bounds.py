"""Export and import bound meshes."""

import bpy
import nose.tools
import os

import io_scene_nif.nif_export
from pyffi.formats.nif import NifFormat
from test import SingleNif
from test.collisions import gen_boundbox


class TestBBox(SingleNif):
    n_name = "collisions/boundbox"
    b_name = "BBoxTest"

    def b_create_objects(self):
        # TODO
        # b_obj = self.b_create_base_geometry()
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects[bpy.context.active_object.name]
        b_obj.name = self.b_name
        b_obj.draw_bounds_type = 'BOX'
        b_obj.draw_type = 'BOUNDS'
        b_obj.data.show_double_sided = False

    def n_create_data(self):
        return gen_boundbox.n_create_data()

    def b_check_data(self):
        b_bbox = bpy.data.objects[self.b_name]
        nose.tools.assert_equal(b_bbox.draw_bounds_type, 'BOX')
        nose.tools.assert_equal(b_bbox.draw_type, 'BOUNDS')

    def n_check_data(self, n_data):
        n_bbox = n_data.roots[0].children[0]
        nose.tools.assert_equal(n_bbox.has_bounding_box, True)

'''
class TestBSBound(TestBaseGeometry):
    n_name = "collisions/boundbox/bsbound"
    b_name = "BSBound"

    def b_create_objects(self):
        b_obj = TestBaseGeometry.b_create_object(self)
        b_obj.name = self.b_name

        b_obj.draw_bounds_type = 'BOX'
        b_obj.draw_type = 'BOUNDS'

        return b_obj



    def b_check_data(self):
        pass


        b_bbox = b_obj[b_name]
        nose.tools.assert_equal(b_bbox.draw_bounds_type, 'BOX')
        nose.tools.assert_equal(b_bbox.draw_type, 'BOUNDS')


    def n_check_data(self, n_data):
        pass


        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(bbox.has_bounding_box, True)

'''
