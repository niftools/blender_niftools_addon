"""Script to import/export all the skeleton related objects."""

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
import bpy
from bpy_extras.io_utils import axis_conversion

from io_scene_nif.modules.nif_export.animation.transform import TransformAnimation
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_global import NifOp
from io_scene_nif.utility.util_logging import NifLog

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
            bind_data[b_bone.name] = (n_bone_bind_scale, n_bone_bind_rot.inverted(), n_bone_bind_trans)
        return bind_data


class Armature:

    def __init__(self):
        self.transform_anim = TransformAnimation()

    def export_bones(self, b_obj, parent_block):
        """Export the bones of an armature."""
        # the armature was already exported as a NiNode
        # now we must export the armature's bones
        assert (b_obj.type == 'ARMATURE')

        b_action = self.transform_anim.get_active_action(b_obj)

        # find the root bones
        # list of all bones
        bones = b_obj.data.bones.values()

        # maps b_bone names to NiNode blocks
        bones_node = {}

        # here all the bones are added
        # first create all bones with their keyframes
        # and then fix the links in a second run

        # ok, let's create the b_bone NiNode blocks
        for b_bone in bones:
            # create a new nif block for this b_bone
            n_bone = self.nif_export.objecthelper.create_ninode(b_bone)
            # doing b_bone map now makes linkage very easy in second run
            bones_node[b_bone.name] = n_bone

            # add the n_bone and the keyframe for this b_bone
            n_bone.name = self.nif_export.objecthelper.get_full_name(b_bone)

            if b_bone.niftools.boneflags != 0:
                n_bone.flags = b_bone.niftools.boneflags
            else:
                if NifOp.props.game in ('OBLIVION', 'FALLOUT_3', 'SKYRIM'):
                    # default for Oblivion bones
                    # note: bodies have 0x000E, clothing has 0x000F
                    n_bone.flags = 0x000E
                elif NifOp.props.game in ('CIVILIZATION_IV', 'EMPIRE_EARTH_II'):
                    if b_bone.children:
                        # default for Civ IV/EE II bones with children
                        n_bone.flags = 0x0006
                    else:
                        # default for Civ IV/EE II final bones
                        n_bone.flags = 0x0016
                elif NifOp.props.game in ('DIVINITY_2',):
                    if b_bone.children:
                        # default for Div 2 bones with children
                        n_bone.flags = 0x0186
                    elif b_bone.name.lower()[-9:] == 'footsteps':
                        n_bone.flags = 0x0116
                    else:
                        # default for Div 2 final bones
                        n_bone.flags = 0x0196
                else:
                    n_bone.flags = 0x0002  # default for Morrowind bones
            # rest pose
            self.nif_export.objecthelper.set_object_matrix(b_bone, n_bone)

            # per-bone animation
            self.transform_anim.export_transforms(n_bone, b_obj, b_action, b_bone)

        # now fix the linkage between the blocks
        for b_bone in bones:
            # link the bone's children to the bone
            NifLog.debug("Linking children of b_bone {0}".format(b_bone.name))
            for child in b_bone.children:
                bones_node[b_bone.name].add_child(bones_node[child.name])
            # if it is a root bone, link it to the armature
            if not b_bone.parent:
                parent_block.add_child(bones_node[b_bone.name])
