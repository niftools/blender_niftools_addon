"""Common methods to related collision"""

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

def b_create_default_collision_properties(b_col_obj):
    """Set the default properties for a collision object"""
    
    b_col_obj.draw_type = 'WIRE' # visual aid, no need to check
    
    b_col_obj.game.use_collision_bounds = True #enable blender visualisation
    b_col_obj.nifcollision.use_blender_properties = True
    b_col_obj.nifcollision.motion_system = "MO_SYS_FIXED"
    b_col_obj.nifcollision.oblivion_layer = "OL_STATIC"
    b_col_obj.nifcollision.col_filter = 0
    b_col_obj.nifcollision.havok_material = "HAV_MAT_WOOD"
    
    
def b_check_default_collision_properties(b_col_obj):
    """Checks the default properties for a collision object"""
    
    nose.tools.assert_equal(b_col_obj.game.use_collision_bounds, True)
    nose.tools.assert_equal(b_col_obj.nifcollision.use_blender_properties, True)
    nose.tools.assert_equal(b_col_obj.nifcollision.motion_system, "MO_SYS_FIXED")
    nose.tools.assert_equal(b_col_obj.nifcollision.oblivion_layer, "OL_STATIC")
    nose.tools.assert_equal(b_col_obj.nifcollision.col_filter, 0)
    nose.tools.assert_equal(b_col_obj.nifcollision.havok_material, "HAV_MAT_WOOD")
    
