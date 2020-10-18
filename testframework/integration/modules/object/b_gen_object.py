"""Helper functions to create and test Blender scene geometry data"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005, NIF File Format Library and Tools contributors.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
# 
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
# 
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

import bpy
from math import radians, degrees
import mathutils

import nose

EPSILON = 0.005
E_VEC = mathutils.Vector((EPSILON, EPSILON, EPSILON))
ZERO = mathutils.Vector((0.0, 0.0, 0.0))

RAD_30 = radians(30.0)
RAD_60 = radians(60.0)
RAD_90 = radians(90.0)


def b_create_transformed_object(b_name):
    """Create and return a single blender object."""
    
    b_obj = b_create_empty_object(b_name)
    b_apply_transform_object(b_obj)
    return b_obj


def b_create_empty_object(b_name):
    """Creates empty object"""

    bpy.ops.object.add(type='EMPTY')
    b_obj = bpy.data.objects[bpy.context.active_object.name]
    b_obj.name = b_name

    return b_obj


def b_apply_transform_object(b_obj):
    """Applies scaling, rotation, translation"""
    
    b_obj.rotation_euler = b_rot_mat().to_euler()
    b_obj.location = b_translation_mat().to_translation()
    b_obj.scale = b_scale_mat().to_scale()


def b_translation_mat():
    # translation
    return mathutils.Matrix.Translation((20, 20, 20))


def b_scale_mat():
    # scale
    return mathutils.Matrix.Scale(0.75, 4)


def b_rot_mat():
    """Return a non-trivial transform matrix."""
    b_rot_mat_x = mathutils.Matrix.Rotation(RAD_30, 4, 'X')
    b_rot_mat_y = mathutils.Matrix.Rotation(RAD_60, 4, 'Y')
    b_rot_mat_z = mathutils.Matrix.Rotation(RAD_90, 4, 'Z')        
    return b_rot_mat_z * b_rot_mat_y * b_rot_mat_x


def b_check_transform(b_obj):
    b_check_matrix_local(b_obj)
    b_check_user_transforms(b_obj)


def b_check_user_transforms(b_obj):
    print(f"b_obj.location - {b_obj.location})"
    nose.tools.assert_equal(b_obj.location, b_translation_mat().to_translation())  # location
    
    print(f"b_obj.scale - {b_obj.scale})"
    nose.tools.assert_equal((b_obj.scale - b_scale_mat().to_scale()) < E_VEC, True)  # uniform scale
    
    b_rot_eul = b_obj.rotation_euler
    print(f"b_rot_eul - {b_rot_eul})"
    b_rot_axis = (degrees(b_rot_eul.x), degrees(b_rot_eul.y), degrees(b_rot_eul.z))
    print(f"b_rot_eul(x,y,z) - {b_rot_axis})"
    nose.tools.assert_equal((b_rot_eul.x - RAD_30) < EPSILON, True)  # x rotation
    nose.tools.assert_equal((b_rot_eul.y - RAD_60) < EPSILON, True)  # y rotation
    nose.tools.assert_equal((b_rot_eul.z - RAD_90) < EPSILON, True)  # z rotation


def b_check_matrix_local(b_obj):
    
    b_loc_vec, b_rot_quat, b_scale_vec = b_obj.matrix_local.decompose()  # transforms   
    
    print(f"b_loc_vec - {b_loc_vec})"
    nose.tools.assert_equal(b_loc_vec, b_translation_mat().to_translation())  # location
    
    print(f"b_scale_vec - {b_scale_vec})"
    nose.tools.assert_equal((b_scale_vec - b_scale_mat().to_scale()) < E_VEC, True)  # uniform scale
    
    b_rot_eul = b_rot_quat.to_euler()
    print(f"b_rot_eul - {b_rot_eul})"
    b_rot_axis = (degrees(b_rot_eul.x), degrees(b_rot_eul.y), degrees(b_rot_eul.z))
    print(f"b_rot_eul(x,y,z) - {b_rot_axis})"
    nose.tools.assert_equal((b_rot_eul.x - RAD_30) < EPSILON, True)  # x rotation
    nose.tools.assert_equal((b_rot_eul.y - RAD_60) < EPSILON, True)  # y rotation
    nose.tools.assert_equal((b_rot_eul.z - RAD_90) < EPSILON, True)  # z rotation
