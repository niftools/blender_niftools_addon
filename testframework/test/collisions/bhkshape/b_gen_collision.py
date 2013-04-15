"""Common methods to related collision"""

import bpy
import mathutils

import nose.tools

from pyffi.formats.nif import NifFormat

HAVOK_SCALE = 7

def b_create_default_collision_properties(b_col_obj):
    """Set the default properties for a collision object"""
    
    b_col_obj.draw_type = 'WIRE' # visual aid, no need to check
    b_col_obj.game.use_collision_bounds = True #also enables BGE visualisation
    b_col_obj.nifcollision.col_filter = 1
    

def b_check_default_collision_properties(b_col_obj):
    """Checks the default properties for a collision object"""
    
    nose.tools.assert_equal(b_col_obj.game.use_collision_bounds, True)
    nose.tools.assert_equal(b_col_obj.nifcollision.col_filter, 1)
    
    
def b_create_translation_matrix():
     #translation
    b_trans_mat = mathutils.Matrix.Translation((20.0, 20.0, 20.0))    
    return b_trans_mat

    
def b_check_translation_matrix(b_obj):
    """Checks that transation is (20,20,20)"""
    b_loc_vec = b_obj.matrix_local.decompose()[0] # transforms
    nose.tools.assert_equal(b_obj.location, mathutils.Vector((20.0, 20.0, 20.0))) # location
    


   
    
