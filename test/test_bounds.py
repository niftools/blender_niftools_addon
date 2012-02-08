"""Export and import bound meshes."""

import bpy
import nose.tools
import os

import io_scene_nif.export_nif
from pyffi.formats.nif import NifFormat
from test.test_cube import TestBaseCube

class TestBound(TestBaseCube):
    n_name = "boundbox/bound_box"
    b_name = "Bounding Box"

    def b_create_object(self):
        b_obj = TestBaseCube.b_create_object(self)
        b_obj.name = b_name
        b_obj.draw_bounds_type = 'BOX'
        b_obj.draw_type = 'BOUNDS'
        return b_obj


    def b_check(self):
        '''
        b_bbox = b_obj[b_name]
        nose.tools.assert_equal(b_bbox.draw_bounds_type, 'BOX')
        nose.tools.assert_equal(b_bbox.draw_type, 'BOUNDS')
        '''
        
    def n_check(self, n_filepath):
        '''
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(bbox.has_bounding_box, True) 
        '''    
        
class TestBSBoundImport(test.Base):
    n_name = "boundbox/bsbound"
    b_name = "BSBound"

    def b_create_object(self):
        b_obj = TestBaseCube.b_create_object(self)
        b_obj.name = b_name
        b_obj.draw_bounds_type = 'BOX'
        b_obj.draw_type = 'BOUNDS'
        return b_obj


    def b_check(self):
        '''
        b_bbox = b_obj[b_name]
        nose.tools.assert_equal(b_bbox.draw_bounds_type, 'BOX')
        nose.tools.assert_equal(b_bbox.draw_type, 'BOUNDS')
        '''
        
    def n_check(self, n_filepath):
        '''
        n_geom = n_data.roots[0].children[0]
        nose.tools.assert_equal(bbox.has_bounding_box, True)
        '''