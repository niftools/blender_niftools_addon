""" Nif Utilities, stores common code that is used across the code base"""


# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
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

import mathutils
from bpy_extras.io_utils import axis_conversion
import math

from io_scene_nif.utility.nif_logging import NifLog


class NifError(Exception):
    """A simple custom exception class for export errors."""
    pass


### do all NIFs use the same coordinate system?
# ZT2 and other old ones
correction = axis_conversion( from_forward="X", from_up="Y" ).to_4x4()
# skyrim
# correction = axis_conversion( from_forward="Z", from_up="Y" ).to_4x4()
correction_inv = correction.inverted()


def import_keymat(rest_rot_inv, key_matrix):
    """
    Handles space conversions for imported keys
    """
    return correction * (rest_rot_inv * key_matrix) * correction_inv
    
def export_keymat(rest_rot, key_matrix, bone):
    """
    Handles space conversions for exported keys
    """
    if bone:
        return rest_rot * (correction_inv * key_matrix * correction)
    else:
        return rest_rot * key_matrix
        

def get_bind_matrix(bone):
    """
    Get a nif armature-space matrix from a blender bone.
    """
    bind = correction *  correction_inv * bone.matrix_local *  correction
    if bone.parent:
        p_bind_restored = correction *  correction_inv * bone.parent.matrix_local *  correction
        bind = p_bind_restored.inverted() * bind
    return bind

def nif_bind_to_blender_bind(nif_armature_space_matrix):
    return correction_inv * correction * nif_armature_space_matrix * correction_inv

def vec_roll_to_mat3(vec, roll):
    #port of the updated C function from armature.c
    #https://developer.blender.org/T39470
    #note that C accesses columns first, so all matrix indices are swapped compared to the C version
    
    nor = vec.normalized()
    THETA_THRESHOLD_NEGY = 1.0e-9
    THETA_THRESHOLD_NEGY_CLOSE = 1.0e-5
    
    #create a 3x3 matrix
    bMatrix = mathutils.Matrix().to_3x3()

    theta = 1.0 + nor[1]

    if (theta > THETA_THRESHOLD_NEGY_CLOSE) or ((nor[0] or nor[2]) and theta > THETA_THRESHOLD_NEGY):

        bMatrix[1][0] = -nor[0]
        bMatrix[0][1] = nor[0]
        bMatrix[1][1] = nor[1]
        bMatrix[2][1] = nor[2]
        bMatrix[1][2] = -nor[2]
        if theta > THETA_THRESHOLD_NEGY_CLOSE:
            #If nor is far enough from -Y, apply the general case.
            bMatrix[0][0] = 1 - nor[0] * nor[0] / theta
            bMatrix[2][2] = 1 - nor[2] * nor[2] / theta
            bMatrix[0][2] = bMatrix[2][0] = -nor[0] * nor[2] / theta
        
        else:
            #If nor is too close to -Y, apply the special case.
            theta = nor[0] * nor[0] + nor[2] * nor[2]
            bMatrix[0][0] = (nor[0] + nor[2]) * (nor[0] - nor[2]) / -theta
            bMatrix[2][2] = -bMatrix[0][0]
            bMatrix[0][2] = bMatrix[2][0] = 2.0 * nor[0] * nor[2] / theta

    else:
        #If nor is -Y, simple symmetry by Z axis.
        bMatrix = mathutils.Matrix().to_3x3()
        bMatrix[0][0] = bMatrix[1][1] = -1.0

    #Make Roll matrix
    rMatrix = mathutils.Matrix.Rotation(roll, 3, nor)
    
    #Combine and output result
    mat = rMatrix * bMatrix
    return mat

def mat3_to_vec_roll(mat):
    #this hasn't changed
    vec = mat.col[1]
    vecmat = vec_roll_to_mat3(mat.col[1], 0)
    vecmatinv = vecmat.inverted()
    rollmat = vecmatinv * mat
    roll = math.atan2(rollmat[0][2], rollmat[2][2])
    return vec, roll

def import_matrix(niBlock, relative_to=None):
    """Retrieves a niBlock's transform matrix as a Mathutil.Matrix."""
    return mathutils.Matrix( niBlock.get_transform(relative_to).as_list() ).transposed()

def decompose_srt(matrix):
    """Decompose Blender transform matrix as a scale, rotation matrix, and
    translation vector."""

    # get matrix components
    trans_vec, rot_quat, scale_vec = matrix.decompose()

    #obtain a combined scale and rotation matrix to test determinate
    rotmat = rot_quat.to_matrix()
    scalemat = mathutils.Matrix(   ((scale_vec[0], 0.0, 0.0),
                                    (0.0, scale_vec[1], 0.0),
                                    (0.0, 0.0, scale_vec[2])) )
    scale_rot = scalemat * rotmat

    # and fix their sign
    if (scale_rot.determinant() < 0): scale_vec.negate()
    # only uniform scaling
    # allow rather large error to accomodate some nifs
    if abs(scale_vec[0]-scale_vec[1]) + abs(scale_vec[1]-scale_vec[2]) > 0.02:
        NifLog.warn("Non-uniform scaling not supported." +
            " Workaround: apply size and rotation (CTRL-A).")
    return [scale_vec[0], rotmat, trans_vec]


def find_property(niBlock, property_type):
    """Find a property."""
    for prop in niBlock.properties:
        if isinstance(prop, property_type):
            return prop
    for prop in niBlock.bs_properties:
        if isinstance(prop, property_type):
            return prop
    return None


def find_controller(niBlock, controller_type):
    """Find a controller."""
    ctrl = niBlock.controller
    while ctrl:
        if isinstance(ctrl, controller_type):
            break
        ctrl = ctrl.next_controller
    return ctrl


def find_extra(niBlock, extratype):
    # TODO: 3.0 - Optimise
    
    """Find extra data."""
    # pre-10.x.x.x system: extra data chain
    extra = niBlock.extra_data
    while extra:
        if isinstance(extra, extratype):
            break
        extra = extra.next_extra_data
    if extra:
        return extra

    # post-10.x.x.x system: extra data list
    for extra in niBlock.extra_data_list:
        if isinstance(extra, extratype):
            return extra
    return None