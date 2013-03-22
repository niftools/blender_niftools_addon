"""Common methods to related collision"""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

def b_create_default_collision_properties(b_col_obj):
    """Set the default properties for a collision object"""
    
    b_col_obj.draw_type = 'WIRE' # visual aid, no need to check
    b_col_obj.game.use_collision_bounds = True #also enables BGE visualisation
    b_col_obj.nifcollision.col_filter = 1
    
    
def b_check_default_collision_properties(b_col_obj):
    """Checks the default properties for a collision object"""
    
    nose.tools.assert_equal(b_col_obj.game.use_collision_bounds, True)
    nose.tools.assert_equal(b_col_obj.nifcollision.col_filter, 1)
   
    
