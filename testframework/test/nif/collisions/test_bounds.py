"""Export and import bound meshes."""

import bpy
import nose.tools
import os

import io_scene_nif.nif_export
from pyffi.formats.nif import NifFormat
from ..geometry.test_geometry import TestBaseGeometry


class TestBound(TestBaseGeometry):
    n_name = "collisions/boundbox/bound_box"
    b_name = "Bounding Box"

    def b_create_objects(self):

        TestBaseGeometry.b_create_objects(self)
        b_obj = bpy.data.objects[self.b_name]
        b_obj.draw_bounds_type = 'BOX'
        b_obj.draw_type = 'BOUNDS'

        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)


    def b_check_data(self):
        pass
        '''
        b_bbox = b_obj[b_name]
        nose.tools.assert_equal(b_bbox.draw_bounds_type, 'BOX')
        nose.tools.assert_equal(b_bbox.draw_type, 'BOUNDS')
        '''
    def n_check_data(self, n_data):
        pass
        '''
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(bbox.has_bounding_box, True)
        '''

'''
class TestBSBound(TestBaseGeometry):
    n_name = "collisions/boundbox/bsbound"
    b_name = "BSBound"

    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self)
        b_obj.name = self.b_name

        b_obj.draw_bounds_type = 'BOX'
        b_obj.draw_type = 'BOUNDS'

        #bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)


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
