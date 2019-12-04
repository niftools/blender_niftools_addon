"""This module contains helper methods to import/export armature data."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2012, NIF File Format Library and Tools contributors.
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
from bpy_extras.io_utils import axis_conversion
from io_scene_nif.utility import nif_utils

B_R_POSTFIX = "].R"
B_L_POSTFIX = "].L"

B_R_SUFFIX = ".R"
B_L_SUFFIX = ".L"

BRACE_L = "[L"
BRACE_R = "[R"

OPEN_BRACKET = "["
CLOSE_BRACKET = "]"

NPC_SUFFIX = "NPC "
NPC_L = "NPC L "
NPC_R = "NPC R "

BIP_01 = "Bip01 "
BIP01_R = "Bip01 R "
BIP01_L = "Bip01 L "


def get_bone_name_for_blender(name):
    """Convert a bone name to a name that can be used by Blender: turns 'Bip01 R xxx' into 'Bip01 xxx.R', and similar for L.

    :param name: The bone name as in the nif file.
    :type name: :class:`str`
    :return: Bone name in Blender convention.
    :rtype: :class:`str`
    """
    if isinstance(name, bytes):
        name = name.decode()
    if name.startswith(BIP01_L):
        name = BIP_01 + name[8:] + B_L_SUFFIX
    elif name.startswith(BIP01_R):
        name = BIP_01 + name[8:] + B_R_SUFFIX
    elif name.startswith(NPC_L) and name.endswith(CLOSE_BRACKET):
        name = replace_nif_name(name, NPC_L, NPC_SUFFIX, BRACE_L, B_L_POSTFIX)
    elif name.startswith(NPC_R) and name.endswith(CLOSE_BRACKET):
        name = replace_nif_name(name, NPC_R, NPC_SUFFIX, BRACE_R, B_R_POSTFIX)
    return name


def replace_nif_name(name, original, replacement, open_replace, close_replace):
    name = name.replace(original, replacement)
    name = name.replace(open_replace, OPEN_BRACKET)
    return name.replace(CLOSE_BRACKET, close_replace)


def get_bone_name_for_nif(name):
    """Convert a bone name to a name that can be used by the nif file: turns 'Bip01 xxx.R' into 'Bip01 R xxx', and similar for L.

    :param name: The bone name as in Blender.
    :type name: :class:`str`
    :return: Bone name in nif convention.
    :rtype: :class:`str`
    """
    if isinstance(name, bytes):
        name = name.decode()
    if name.startswith(BIP_01):
        if name.endswith(B_L_SUFFIX):
            name = BIP01_L + name[6:-2]
        elif name.endswith(B_R_SUFFIX):
            name = BIP01_R + name[6:-2]
    elif name.startswith(NPC_SUFFIX) and name.endswith(B_L_POSTFIX):
        name = replace_blender_name(name, NPC_SUFFIX, NPC_L, BRACE_L, B_L_POSTFIX)
    elif name.startswith(NPC_SUFFIX) and name.endswith(B_R_POSTFIX):
        name = replace_blender_name(name, NPC_SUFFIX, NPC_R, BRACE_R, B_R_POSTFIX)
    return name


def replace_blender_name(name, original, replacement, open_replace, close_replace):
    name = name.replace(original, replacement)
    name = name.replace(OPEN_BRACKET, open_replace)
    return name.replace(close_replace, CLOSE_BRACKET)


def set_bone_orientation(from_forward, from_up):
    # if version in (0x14020007, ):
    #   skyrim
    #   from_forward = "Z"
    #   from_up = "Y"
    # else:
    #   ZT2 and other old ones
    #   from_forward = "X"
    #   from_up = "Y"
    global correction
    global correction_inv
    correction = axis_conversion(from_forward, from_up).to_4x4()
    correction_inv = correction.inverted()


# set these from outside using set_bone_correction_from_version once we have a version number
correction = None
correction_inv = None


def import_keymat(rest_rot_inv, key_matrix):
    """Handles space conversions for imported keys """
    return correction * (rest_rot_inv * key_matrix) * correction_inv


def export_keymat(rest_rot, key_matrix, bone):
    """Handles space conversions for exported keys """
    if bone:
        return rest_rot * (correction_inv * key_matrix * correction)
    else:
        return rest_rot * key_matrix


def get_bind_matrix(bone):
    """Get a nif armature-space matrix from a blender bone. """
    bind = correction * correction_inv * bone.matrix_local * correction
    if bone.parent:
        p_bind_restored = correction * correction_inv * bone.parent.matrix_local * correction
        bind = p_bind_restored.inverted() * bind
    return bind


def nif_bind_to_blender_bind(nif_armature_space_matrix):
    return correction_inv * correction * nif_armature_space_matrix * correction_inv


def get_armature():
    """Get an armature. If there is more than one armature in the scene and some armatures are selected, return the first of the selected armatures. """
    src_armatures = [ob for ob in bpy.data.objects if type(ob.data) == bpy.types.Armature]
    # do we have armatures?
    if src_armatures:
        # see if one of these is selected -> get only that one
        if len(src_armatures) > 1:
            sel_armatures = [ob for ob in src_armatures if ob.select]
            if sel_armatures:
                return sel_armatures[0]
        return src_armatures[0]


def get_bind_data(b_armature):
    """Get the required bind data of an armature. Used by standalone KF import and export. """
    if b_armature:
        bind_data = {}
        for b_bone in b_armature.data.bones:
            n_bone_bind_scale, n_bone_bind_rot, n_bone_bind_trans = nif_utils.decompose_srt(get_bind_matrix(b_bone))
            bind_data[b_bone.name] = (n_bone_bind_scale, n_bone_bind_rot.to_4x4().inverted(), n_bone_bind_trans)
        return bind_data
