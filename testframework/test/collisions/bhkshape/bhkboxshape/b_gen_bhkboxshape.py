"""Methods to test bhkboxshape."""

import bpy
import nose.tools

def b_create_bhkboxshape_properties(b_col_obj):
    """Set the object to be Box Collision."""
    
    b_col_obj.nifcollision.oblivion_layer = "OL_CLUTTER" # 4
    b_col_obj.nifcollision.motion_system = "MO_SYS_BOX" # 4
    b_col_obj.nifcollision.quality_type = "MO_QUAL_MOVING" # 4
    
    b_col_obj.game.collision_bounds_type = 'BOX'
    b_col_obj.nifcollision.havok_material = "HAV_MAT_WOOD" # 9
    
    
def b_check_bhkboxshape_properties(b_col_obj):
    """Check the box collision related property."""
    #bhkrigidbody
    nose.tools.assert_equal(b_col_obj.nifcollision.oblivion_layer, "OL_CLUTTER") # 4
    nose.tools.assert_equal(b_col_obj.nifcollision.motion_system, "MO_SYS_BOX") # 4
    nose.tools.assert_equal(b_col_obj.nifcollision.quality_type , "MO_QUAL_MOVING") # 4
    
    #bhkshape
    nose.tools.assert_equal(b_col_obj.game.collision_bounds_type, 'BOX')
    nose.tools.assert_equal(b_col_obj.nifcollision.havok_material, "HAV_MAT_WOOD") # 9