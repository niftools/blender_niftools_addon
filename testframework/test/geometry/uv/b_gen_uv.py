import bpy
import math
import mathutils

import nose

def b_uv_object():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, use_subsurf_data=False, uv_subsurf_level=1)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    
