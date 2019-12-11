""" Nif Utilities, stores common code that is used across the code base"""
# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2013, NIF File Format Library and Tools contributors.
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

import math

import mathutils

from io_scene_nif.utility.util_logging import NifLog


class NifError(Exception):
    """A simple custom exception class for export errors."""
    pass


def vec_roll_to_mat3(vec, roll):
    # port of the updated C function from armature.c
    # https://developer.blender.org/T39470
    # note that C accesses columns first, so all matrix indices are swapped compared to the C version

    nor = vec.normalized()
    THETA_THRESHOLD_NEGY = 1.0e-9
    THETA_THRESHOLD_NEGY_CLOSE = 1.0e-5

    # create a 3x3 matrix
    bMatrix = mathutils.Matrix().to_3x3()

    theta = 1.0 + nor[1]

    if (theta > THETA_THRESHOLD_NEGY_CLOSE) or ((nor[0] or nor[2]) and theta > THETA_THRESHOLD_NEGY):

        bMatrix[1][0] = -nor[0]
        bMatrix[0][1] = nor[0]
        bMatrix[1][1] = nor[1]
        bMatrix[2][1] = nor[2]
        bMatrix[1][2] = -nor[2]
        if theta > THETA_THRESHOLD_NEGY_CLOSE:
            # If nor is far enough from -Y, apply the general case.
            bMatrix[0][0] = 1 - nor[0] * nor[0] / theta
            bMatrix[2][2] = 1 - nor[2] * nor[2] / theta
            bMatrix[0][2] = bMatrix[2][0] = -nor[0] * nor[2] / theta

        else:
            # If nor is too close to -Y, apply the special case.
            theta = nor[0] * nor[0] + nor[2] * nor[2]
            bMatrix[0][0] = (nor[0] + nor[2]) * (nor[0] - nor[2]) / -theta
            bMatrix[2][2] = -bMatrix[0][0]
            bMatrix[0][2] = bMatrix[2][0] = 2.0 * nor[0] * nor[2] / theta

    else:
        # If nor is -Y, simple symmetry by Z axis.
        bMatrix = mathutils.Matrix().to_3x3()
        bMatrix[0][0] = bMatrix[1][1] = -1.0

    # Make Roll matrix
    rMatrix = mathutils.Matrix.Rotation(roll, 3, nor)

    # Combine and output result
    mat = rMatrix * bMatrix
    return mat


def mat3_to_vec_roll(mat):
    # this hasn't changed
    vec = mat.col[1]
    vecmat = vec_roll_to_mat3(mat.col[1], 0)
    vecmatinv = vecmat.inverted()
    rollmat = vecmatinv * mat
    roll = math.atan2(rollmat[0][2], rollmat[2][2])
    return vec, roll


def import_matrix(n_block, relative_to=None):
    """Retrieves a n_block's transform matrix as a Mathutil.Matrix."""
    return mathutils.Matrix(n_block.get_transform(relative_to).as_list()).transposed()


def decompose_srt(b_matrix):
    """Decompose Blender transform matrix as a scale, 4x4 rotation matrix, and translation vector."""

    # get matrix components
    trans_vec, rot_quat, scale_vec = b_matrix.decompose()
    rotmat = rot_quat.to_matrix()

    # todo [armature] negative scale is not generated on armature end
    #                 no need to run costly operations here for now
    # and fix the sign of scale
    # if b_matrix.determinant() < 0:
    #     scale_vec.negate()

    # only uniform scaling allow rather large error to accommodate some nifs
    if abs(scale_vec[0] - scale_vec[1]) + abs(scale_vec[1] - scale_vec[2]) > 0.02:
        NifLog.warn("Non-uniform scaling not supported. Workaround: apply size and rotation (CTRL-A).")
    return scale_vec[0], rotmat.to_4x4(), trans_vec


def find_property(n_block, property_type):
    """Find a property."""
    if hasattr(n_block, "properties"):
        for prop in n_block.properties:
            if isinstance(prop, property_type):
                return prop

    if hasattr(n_block, "bs_properties"):
        for prop in n_block.bs_properties:
            if isinstance(prop, property_type):
                return prop
    return None


def find_controller(n_block, controller_type):
    """Find a controller."""
    ctrl = n_block.controller
    while ctrl:
        if isinstance(ctrl, controller_type):
            break
        ctrl = ctrl.next_controller
    return ctrl


def find_extra(n_block, extratype):
    # TODO: 3.0 - Optimise

    """Find extra data."""
    # pre-10.x.x.x system: extra data chain
    extra = n_block.extra_data
    while extra:
        if isinstance(extra, extratype):
            break
        extra = extra.next_extra_data
    if extra:
        return extra

    # post-10.x.x.x system: extra data list
    for extra in n_block.extra_data_list:
        if isinstance(extra, extratype):
            return extra
    return None
