"""Methods to test bhkboxshape."""

import bpy
import nose.tools

def b_create_bhkboxshape_properties(b_col_obj):
    """Set the object to be Box Collision."""
    
    b_col_obj.game.collision_bounds_type = 'BOX'
    
    
def b_check_bhkboxshape_properties(b_col_obj):
    """Check the box collision related property."""
    
    nose.tools.assert_equal(b_col_obj.game.collision_bounds_type, 'BOX')