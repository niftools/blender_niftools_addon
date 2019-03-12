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

import bpy
from bpy_extras.io_utils import axis_conversion
from io_scene_nif.utility import nif_utils

# dictionary of bones that belong to a certain armature
# maps NIF armature name to list of NIF bone name
DICT_ARMATURES = {}

# bone animation priorities (maps NiNode name to priority number);
# priorities are set in import_kf_root and are stored into the name
# of a NULL constraint (for lack of something better) in
# import_armature
DICT_BONE_PRIORITIES = {}


def get_bone_name_for_blender(name):
    """Convert a bone name to a name that can be used by Blender: turns
    'Bip01 R xxx' into 'Bip01 xxx.R', and similar for L.

    :param name: The bone name as in the nif file.
    :type name: :class:`str`
    :return: Bone name in Blender convention.
    :rtype: :class:`str`
    """
    if isinstance(name, bytes):
        name = name.decode()
    if name.startswith("Bip01 L "):
        return "Bip01 " + name[8:] + ".L"
    elif name.startswith("Bip01 R "):
        return "Bip01 " + name[8:] + ".R"
    elif name.startswith("NPC L ") and name.endswith("]"):
        name = name.replace("NPC L", "NPC")
        name = name.replace("[L", "[")
        name = name.replace("]", "].L")
        return name
    elif name.startswith("NPC R ") and name.endswith("]"):
        name = name.replace("NPC R", "NPC")
        name = name.replace("[R", "[")
        name = name.replace("]", "].R")
        return name

    return name


def get_bone_name_for_nif(name):
    """Convert a bone name to a name that can be used by the nif file:
    turns 'Bip01 xxx.R' into 'Bip01 R xxx', and similar for L.

    :param name: The bone name as in Blender.
    :type name: :class:`str`
    :return: Bone name in nif convention.
    :rtype: :class:`str`
    """
    if isinstance(name, bytes):
        name = name.decode()
    if name.startswith("Bip01 "):
        if name.endswith(".L"):
            return "Bip01 L " + name[6:-2]
        elif name.endswith(".R"):
            return "Bip01 R " + name[6:-2]
    elif name.startswith("NPC ") and name.endswith("].L"):
        name = name.replace("NPC ", "NPC L")
        name = name.replace("[", "[L")
        name = name.replace("].L", "]")
        return name
    elif name.startswith("NPC ") and name.endswith("].R"):
        name = name.replace("NPC ", "NPC R")
        name = name.replace("[", "[R")
        name = name.replace("].R", "]")
        return name
    return name

def set_bone_orientation(from_forward, from_up):
    # if version in (0x14020007, ):
        # # skyrim
        # from_forward = "Z"
        # from_up = "Y"
    # else:
        # ZT2 and other old ones
        # from_forward = "X"
        # from_up = "Y"
    global correction
    global correction_inv
    correction = axis_conversion( from_forward, from_up ).to_4x4()
    correction_inv = correction.inverted()

#set these from outside using set_bone_correction_from_version once we have a version number
correction = None
correction_inv = None


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
    
def get_armature():
    """
    Get an armature.
    If there is more than one armature in the scene and some armatures are selected, return the first of the selected armatures.
    """
    src_armatures = [ob for ob in bpy.data.objects if type(ob.data) == bpy.types.Armature]
    #do we have armatures?
    if src_armatures:
        #see if one of these is selected -> get only that one
        if len(src_armatures) > 1:
            sel_armatures = [ob for ob in src_armatures if ob.select]
            if sel_armatures:
                return sel_armatures[0]
        return src_armatures[0]
        
def get_bind_data(b_armature):
    """
    Get the required bind data of an armature.
    Used by standalone KF import and export.
    """
    if b_armature:
        bind_data = {}
        for b_bone in b_armature.data.bones:
            niBone_bind_scale, niBone_bind_rot, niBone_bind_trans = nif_utils.decompose_srt( get_bind_matrix(b_bone) )
            bind_data[b_bone.name] = (niBone_bind_scale, niBone_bind_rot.to_4x4().inverted(), niBone_bind_trans)
        return bind_data