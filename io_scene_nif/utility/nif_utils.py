''' Nif Utilities, stores common code that is used across the code base'''


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


class NifError(Exception):
    """A simple custom exception class for export errors."""
    pass


def import_matrix(niBlock, relative_to=None):
    """Retrieves a niBlock's transform matrix as a Mathutil.Matrix."""
    # return Matrix(*niBlock.get_transform(relative_to).as_list())
    n_scale, n_rot_mat3, n_loc_vec3 = niBlock.get_transform(relative_to).get_scale_rotation_translation()

    # create a location matrix
    b_loc_vec = mathutils.Vector(n_loc_vec3.as_tuple())
    b_loc_vec = mathutils.Matrix.Translation(b_loc_vec)

    # create a scale matrix
    b_scale_mat = mathutils.Matrix.Scale(n_scale, 4)

    # create 3 rotation matrices
    n_rot_mat = mathutils.Matrix()
    n_rot_mat[0].xyz = n_rot_mat3.m_11, n_rot_mat3.m_21, n_rot_mat3.m_31
    n_rot_mat[1].xyz = n_rot_mat3.m_12, n_rot_mat3.m_22, n_rot_mat3.m_32
    n_rot_mat[2].xyz = n_rot_mat3.m_13, n_rot_mat3.m_23, n_rot_mat3.m_33
    b_rot_mat = n_rot_mat * b_scale_mat.transposed()

    b_import_matrix = b_loc_vec * b_rot_mat * b_scale_mat
    return b_import_matrix


def decompose_srt(matrix):
    """Decompose Blender transform matrix as a scale, rotation matrix, and
    translation vector."""

    # get scale components
    trans_vec, rot_quat, scale_vec = matrix.decompose()
    scale_rot = rot_quat.to_matrix()
    b_scale = mathutils.Vector((scale_vec[0] ** 0.5,
                                scale_vec[1] ** 0.5,
                                scale_vec[2] ** 0.5)
                               )
    # and fix their sign
    if (scale_rot.determinant() < 0):
        b_scale.negate()
    # only uniform scaling
    # allow rather large error to accomodate some nifs
    if abs(scale_vec[0] - scale_vec[1]) + abs(scale_vec[1] - scale_vec[2]) > 0.02:
        raise NifError("Non-uniform scaling not supported. Workaround: apply size and rotation (CTRL-A).")
    b_scale = b_scale[0]
    b_rot = scale_rot * b_scale
    b_trans = trans_vec
    return [b_scale, b_rot, b_trans]


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
